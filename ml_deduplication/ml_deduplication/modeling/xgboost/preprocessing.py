import logging

import polars as pl
from ml_deduplication.modeling.xgboost.blocking import block_df
from ml_deduplication.modeling.xgboost.features_engineering import generate_features
from sentence_transformers import SentenceTransformer

logger = logging.getLogger(__name__)


def strip_ville_from_name(data: dict) -> str:
    if (data["ville"] is None) or (data["ville"].strip() == ""):
        return data["nom"]
    nom_clean = data["nom"].replace(data["ville"].strip(), "")

    if data["ville_clean"] is not None:
        nom_clean = data["nom"].replace(data["ville_clean"].strip(), "")

    return nom_clean


def preprocess_features(
    df_features: pl.DataFrame,
    embedding_model: SentenceTransformer,
    df_embeddings: pl.DataFrame | None = None,
) -> pl.DataFrame:
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

    return df_features_preprocessed


def preprocess_entities_df(
    df_entities: pl.DataFrame,
    embedding_model: SentenceTransformer,
    include_label: bool = True,
    additional_columns_to_keep: None | list[str] = None,
    additional_business_rules_exprs: list[pl.Expr] | None = None,
    df_embeddings: pl.DataFrame | None = None,
) -> pl.DataFrame | tuple[pl.DataFrame, pl.DataFrame]:
    logger.info("Starting data preprocessing...")
    df_features_preprocessed = preprocess_features(
        df_entities, embedding_model, df_embeddings
    )

    df_pairs = block_df(df_features_preprocessed, additional_business_rules_exprs)
    df_pairs_features = generate_features(
        df_pairs, include_label, additional_columns_to_keep
    )

    X = df_pairs_features

    if include_label:
        y = df_pairs_features.select(pl.col("label"))
        return X.select(pl.selectors.exclude("label")), y

    logger.info("Finished data processing.")
    return X
