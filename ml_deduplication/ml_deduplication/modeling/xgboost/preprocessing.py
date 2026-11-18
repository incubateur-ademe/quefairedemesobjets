import logging
from collections.abc import Generator

import duckdb
import polars as pl
from sentence_transformers import SentenceTransformer

from ml_deduplication.modeling.xgboost.blocking import (
    run_blocking,
)
from ml_deduplication.modeling.xgboost.features_engineering import (
    generate_features,
)
from ml_deduplication.modeling.xgboost.schema import OPTIMIZED_SCHEMA
from ml_deduplication.modeling.xgboost.utils import (
    get_features_df_batches_from_duckdb,
    get_features_df_from_duckdb,
    load_df_acteurs_to_duckdb,
)

logger = logging.getLogger(__name__)


def strip_ville_from_name(data: dict) -> str:
    """Remove the city name from an entity's concatenated name.

    Given a dict holding the cleaned name, the raw city name and the cleaned
    city name, remove any occurrence of the city from the name. This avoids
    duplicating the city information that is already stored in a dedicated
    column.

    Parameters
    ----------
    data : dict
        Mapping with keys ``nom``, ``ville`` and ``ville_clean``. ``nom`` is the
        concatenation of the nominal and commercial names. ``ville`` is the raw
        (possibly hyphenated) city name; ``ville_clean`` is its normalised form
        (lowercased, ``st`` expanded to ``saint``, hyphens replaced by spaces).

    Returns
    -------
    str
        The ``nom`` value with the city name removed. If ``ville`` is ``None``
        or empty, ``nom`` is returned unchanged.
    """
    if (data["ville"] is None) or (data["ville"].strip() == ""):
        return data["nom"]
    nom_clean = data["nom"].replace(data["ville"].strip(), "")

    if data["ville_clean"] is not None:
        nom_clean = data["nom"].replace(data["ville_clean"].strip(), "")

    return nom_clean


def preprocess_features(
    df_features: pl.DataFrame,
    embedding_model: SentenceTransformer | None = None,
    df_embeddings: pl.DataFrame | None = None,
) -> pl.DataFrame:

    if all(e is None for e in [embedding_model, df_embeddings]):
        raise ValueError(
            "Please provide either an embedding model or a dataframe containing precomputed embeddings."
        )

    df_features_preprocessed = df_features.clone()

    df_features_preprocessed = df_features_preprocessed.with_columns(
        pl.selectors.by_dtype(pl.String)
        .exclude(["cluster_id", "cluster_id_split", "label"])
        .str.strip_chars()
        .replace("__empty__", None)
        .replace("", None)
    )
    str_column_to_process = [
        "nom",
        "nom_commercial",
        "ville",
    ]

    df_features_preprocessed = (
        df_features_preprocessed.with_columns(
            pl.col(e)
            .str.strip_chars()
            .str.to_lowercase()
            .str.normalize("NFKD")
            .map_elements(lambda x: x.encode("ASCII", "ignore").decode("utf-8"))
            for e in str_column_to_process
        )
        .with_columns(
            pl.col("ville")
            .str.replace_all("st", "saint", literal=True)
            .str.replace_all("-", " ", literal=True)
            .alias("ville_clean")
        )
        .with_columns(
            pl.selectors.starts_with("latitude").clip(-90.0, 90.0),
            pl.selectors.starts_with("longitude").clip(-180.0, 180.0),
            pl.struct(
                pl.concat_str(
                    "nom", "nom_commercial", separator=" ", ignore_nulls=True
                ).alias("nom"),
                "ville",
                "ville_clean",
            )
            .map_elements(strip_ville_from_name, return_dtype=pl.String)
            .alias(
                "nom_clean"
            ),  # Concatenate nom and nom_commercial and eliminate ville from nom
            pl.concat_str(
                pl.col("adresse").fill_null(""),
                pl.col("adresse_complement").fill_null(""),
                separator=" ",
            ).alias(
                "adresse_clean"
            ),  # Concatenate adresse and adresse_complement
            pl.coalesce(["nom", "nom_commercial"]).alias("nom"),
            pl.coalesce(["nom_commercial", "nom"]).alias("nom_commercial"),
        )
    )

    addresses_texts = df_features_preprocessed.get_column("adresse_clean").to_list()

    if df_embeddings is None:
        addresses_tensors = embedding_model.encode(addresses_texts)
        df_vectors = pl.DataFrame({"adresse_clean_vector": addresses_tensors})
        df_features_preprocessed = pl.concat(
            [df_features_preprocessed, df_vectors], how="horizontal"
        )
    else:
        df_features_preprocessed = df_features_preprocessed.join(
            df_embeddings, on="identifiant_unique", how="left"
        )

    df_features_preprocessed = df_features_preprocessed.with_columns(
        pl.when(pl.col("adresse").is_null() & pl.col("adresse_complement").is_null())
        .then(None)
        .otherwise(pl.col("adresse_clean_vector").cast(pl.Array(pl.Float32, 1024)))
        .alias("adresse_clean_vector")
    )

    optimized_schema = OPTIMIZED_SCHEMA
    df_features_preprocessed = df_features_preprocessed.with_columns(
        pl.col(k).cast(v)
        for k, v in optimized_schema.items()
        if k in df_features_preprocessed.columns
    )

    return df_features_preprocessed


def _run_preprocessing_pipeline(
    df_entities: pl.DataFrame,
    embedding_model: SentenceTransformer,
    duckdb_con: duckdb.DuckDBPyConnection,
    include_label: bool,
    additional_columns_to_keep: None | list[str],
    additional_business_rules_sql_exprs: list[str] | None,
    df_embeddings: pl.DataFrame | None,
) -> int | None:
    """Run preprocess + blocking + feature generation inside ``duckdb_con``.

    Leaves the ``pairs_features`` table materialized in duckdb (dropping the
    intermediate ``pairs`` / ``features`` tables). Returns the number of
    candidate pairs, or ``None`` when no candidates were found so the caller can
    short-circuit before reading the feature table.
    """
    logger.info("Starting data preprocessing...")
    df_features_preprocessed = preprocess_features(
        df_entities, embedding_model, df_embeddings
    )

    additional_columns_to_keep = additional_columns_to_keep or []
    load_df_acteurs_to_duckdb(
        con=duckdb_con,
        df_acteurs=df_features_preprocessed,
        additional_columns_to_keep=additional_columns_to_keep,
    )

    logger.info("Starting blocking...")
    num_candidates = run_blocking(
        duckdb_con,
        additional_business_rules_sql_exprs,
    )
    logger.info("Finished blocking.")
    if num_candidates == 0:
        return None
    logger.info("Starting generating features...")

    generate_features(
        duckdb_con,
        include_label,
        additional_columns_to_keep,
    )
    logger.info("Finished generating features.")
    return num_candidates


def preprocess_entities_df(
    df_entities: pl.DataFrame,
    embedding_model: SentenceTransformer,
    duckdb_con: duckdb.DuckDBPyConnection,
    include_label: bool = True,
    additional_columns_to_keep: None | list[str] = None,
    additional_business_rules_sql_exprs: list[str] | None = None,
    df_embeddings: pl.DataFrame | None = None,
) -> pl.DataFrame | tuple[pl.DataFrame, pl.DataFrame] | None:
    """Build the frame ready to be scored in a single pass (no batching).

    Runs preprocessing, blocking and feature generation inside ``duckdb_con``,
    then returns the materialized feature frame. Returns ``None`` when no
    candidate pairs were found. When ``include_label`` is ``True``, returns a
    ``(X, y)`` tuple; otherwise the plain feature frame ``X``.
    """
    n = _run_preprocessing_pipeline(
        df_entities,
        embedding_model,
        duckdb_con,
        include_label,
        additional_columns_to_keep,
        additional_business_rules_sql_exprs,
        df_embeddings,
    )
    if n is None:
        return None

    logger.info("Reading features from duckdb...")
    df_pairs_features = get_features_df_from_duckdb(duckdb_con)
    logger.info("Finished data processing.")
    X = df_pairs_features.select(pl.selectors.exclude("label"))
    if include_label:
        y = df_pairs_features.select(pl.col("label"))
        return X, y
    return X


def preprocess_entities_df_batched(
    df_entities: pl.DataFrame,
    embedding_model: SentenceTransformer,
    duckdb_con: duckdb.DuckDBPyConnection,
    include_label: bool = True,
    additional_columns_to_keep: None | list[str] = None,
    additional_business_rules_sql_exprs: list[str] | None = None,
    df_embeddings: pl.DataFrame | None = None,
    batch_size: int = 1_000_000,
) -> Generator[pl.DataFrame | tuple[pl.DataFrame, pl.DataFrame]]:
    """Yield candidate-pair feature batches from a single duckdb blocking pass.

    Builds the ``pairs_features`` table once inside ``duckdb_con``, then streams
    it in ordered Arrow record batches of ``batch_size`` rows, converted on the
    fly to polars. Each yielded item is ``(X, y)`` when ``include_label`` is
    ``True``, otherwise just ``X`` (the ``label`` column excluded). If no
    candidate pairs are found, the generator yields nothing. This keeps the
    heavy features matrix bounded in memory regardless of the total number of
    candidate pairs.
    """
    n = _run_preprocessing_pipeline(
        df_entities,
        embedding_model,
        duckdb_con,
        include_label,
        additional_columns_to_keep,
        additional_business_rules_sql_exprs,
        df_embeddings,
    )
    if n is None:
        return

    logger.info("Streaming features from duckdb in batches of %d...", batch_size)
    for batch_arrow in get_features_df_batches_from_duckdb(
        duckdb_con, batch_size=batch_size
    ):
        X = batch_arrow.select(pl.selectors.exclude("label"))
        if include_label:
            y = batch_arrow.select(pl.col("label"))
            yield X, y
        else:
            yield X
    logger.info("Finished data processing.")
