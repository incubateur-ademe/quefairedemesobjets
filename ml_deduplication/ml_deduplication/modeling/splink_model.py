"""Splink-based deduplication model with business rules support."""

import logging
from pathlib import Path

import duckdb
import polars as pl
from altair import Chart
from ml_deduplication.training.utils import split_train_dev
from sentence_transformers import SentenceTransformer
from splink import DuckDBAPI, Linker, SettingsCreator

logger = logging.getLogger(__name__)


def create_ducbdb_backend(tmp_dir: Path | None = None) -> DuckDBAPI:
    con = duckdb.connect()
    con.install_extension("spatial")
    con.load_extension("spatial")

    if tmp_dir is not None:
        con.sql(f"SET temp_directory = '{tmp_dir.absolute()}' ")

    db_api = DuckDBAPI(connection=con)
    return db_api


def features_to_entities_df(
    df_features: pl.DataFrame,
) -> tuple[pl.DataFrame, list[str]]:
    """Pivot pair-level features into one-row-per-entity format.

    Parameters
    ----------
    df_features : pl.DataFrame
        Features dataframe with _i / _j suffixed columns for each entity in a pair.

    Returns
    -------
    entities_df : pl.DataFrame
        One row per unique entity_id, with feature values from whichever side they appeared on.
    all_feature_cols : list[str]
        List of feature column names (without suffixes).
    """
    # Identify _i and _j columns by stripping the trailing '_i' or '_j'.
    i_columns = {c[:-2] for c in df_features.columns if c.endswith("_i")}
    j_columns = {c[:-2] for c in df_features.columns if c.endswith("_j")}

    shared_cols = (i_columns & j_columns) - {"identifiant_unique"}
    feature_names = sorted(shared_cols)

    logger.debug(
        "Entities will have %d features: %s", len(feature_names), feature_names[:10]
    )

    i_df = df_features.select(
        pl.col("identifiant_unique_i").alias("entity_id"),
        pl.col("cluster_id"),
        pl.col("split"),
        pl.col("cluster_id_split"),
        *[pl.col(f"{f}_i").alias(f) for f in feature_names],
    )

    j_df = df_features.select(
        pl.col("identifiant_unique_j").alias("entity_id"),
        pl.col("cluster_id"),
        pl.col("split"),
        pl.col("cluster_id_split"),
        *[pl.col(f"{f}_j").alias(f) for f in feature_names],
    )

    # Union and keep first occurrence (entities may appear on both sides of different pairs).
    entities_df = (
        pl.concat([i_df, j_df])
        .group_by("entity_id")
        .agg(
            *[pl.first(f) for f in feature_names],
            pl.first("cluster_id"),
            pl.first("split"),
            pl.first("cluster_id_split"),
        )
    )

    logger.debug("Created entities DataFrame with shape %s", entities_df.shape)

    return entities_df, feature_names


def strip_ville_from_name(data: dict) -> str:
    if (data["ville"] is None) or (data["ville"].strip() == ""):
        return data["nom"]

    return data["nom"].replace(data["ville"].strip(), "")


class BusinessRulesSplink:
    """Wraps Splink's probabilistic linkage with business rules filtering."""

    business_rules_fragment = """AND
    (
        (
            (l.acteur_type_id = r.acteur_type_id)
            OR (l.acteur_type_id = 4 AND r.acteur_type_id = 3)
            OR (l.acteur_type_id = 3 AND r.acteur_type_id = 4)
        )
        AND (l.source_id!=r.source_id)
    )"""

    def __init__(
        self,
        splink_settings: SettingsCreator,
        embedding_model: SentenceTransformer,
        db_api: DuckDBAPI | None = None,
        df_features: pl.DataFrame | None = None,
        unique_fields=("source_id",),
        distinct_fields=("acteur_type_id",),
    ):

        self.splink_settings = splink_settings
        self.embedding_model = embedding_model

        self.linker = None

        if (db_api is not None) and (df_features is not None):
            df_features = df_features.rename(
                {"cluster_id": "cluster_id_true"}, strict=False
            )
            df_features_preprocessed = self.preprocess_features(df_features)

            self.linker = Linker(
                df_features_preprocessed,  # type: ignore
                splink_settings,
                db_api=db_api,
            )

        self._unique_fields = unique_fields
        self._distinct_fields = distinct_fields

        self.validation_chart: None | Chart = None
        self.waterfall_chart_data: None | list[dict] = None
        self.waterfall_chart: None | Chart = None

    def preprocess_features(self, df_features: pl.DataFrame) -> pl.DataFrame:
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

        df_features_preprocessed = df_features_preprocessed.with_columns(
            pl.col(e)
            .str.to_lowercase()
            .str.normalize("NFKD")
            .map_elements(lambda x: x.encode("ASCII", "ignore").decode("utf-8"))
            for e in str_column_to_process
        ).with_columns(
            pl.selectors.starts_with("latitude").clip(-90.0, 90.0),
            pl.selectors.starts_with("longitude").clip(-180.0, 180.0),
            pl.struct(
                pl.concat_str(
                    "nom", "nom_commercial", separator=" ", ignore_nulls=True
                ).alias("nom"),
                "ville",
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

        addresses_texts = df_features_preprocessed.get_column("adresse_clean").to_list()

        addresses_tensors = self.embedding_model.encode(addresses_texts)

        df_vectors = pl.DataFrame({"adresse_clean_vector": addresses_tensors})
        df_features_preprocessed = pl.concat(
            [df_features_preprocessed, df_vectors], how="horizontal"
        ).with_columns(
            pl.when(
                pl.col("adresse").is_null() & pl.col("adresse_complement").is_null()
            )
            .then(None)
            .otherwise(pl.col("adresse_clean_vector").cast(pl.Array(pl.Float64, 1024)))
            .alias("adresse_clean_vector")
        )

        return df_features_preprocessed

    def fit_linker(self):
        deterministic_rules = [
            "(l.nom == r.nom)"
            "AND (l.adresse == r.adresse)"
            "AND (l.ville == r.ville)" + self.business_rules_fragment,
            "(l.siret == r.siret)"
            "AND (l.adresse == r.adresse)"
            "AND (l.ville == r.ville)" + self.business_rules_fragment,
            "(l.nom_commercial == r.nom_commercial)"
            "AND (l.adresse == r.adresse)"
            "AND (l.ville == r.ville)" + self.business_rules_fragment,
        ]

        self.linker.training.estimate_probability_two_random_records_match(  # type: ignore
            deterministic_rules,  # type: ignore
            recall=0.8,
        )
        self.linker.training.estimate_u_using_random_sampling(max_pairs=1e9)  # type: ignore
        self.linker.training.estimate_m_from_label_column("cluster_id_true")  # type: ignore

        return self.linker

    def train(
        self,
        df_features_train: pl.DataFrame,
        min_precision: float = 0.95,
    ):  # type: ignore[reportUnknownParameterType]
        """Train the Splink model from labeled pair data."""

        # Split train/dev for threshold selection
        df_train_sub, df_dev = split_train_dev(df_features_train)

        df_train_sub = df_train_sub.rename({"cluster_id": "cluster_id_true"})

        # preprocessing df_train

        df_train_sub_preprocessed = self.preprocess_features(df_train_sub)

        # Create training linker
        db_api_train_sub = create_ducbdb_backend(Path("/Volumes/PRO-G40"))
        self.linker = Linker(
            df_train_sub_preprocessed,  # type: ignore
            self.splink_settings,
            db_api_train_sub,
        )
        # Train linker
        self.fit_linker()

        # Dev evaluation
        ## dev preprocessing
        df_dev = df_dev.rename({"cluster_id": "cluster_id_true"})
        df_dev_preprocessed = self.preprocess_features(df_dev)

        ## Create new linker object
        db_api_dev = create_ducbdb_backend(Path("/Volumes/PRO-G40"))
        linker_dev = Linker(
            df_dev_preprocessed,  # type: ignore
            self.linker.misc.save_model_to_json(),
            db_api_dev,
        )

        self.validation_chart = (
            linker_dev.evaluation.accuracy_analysis_from_labels_column(
                labels_column_name="cluster_id_true", add_metrics=["f1", "f0_5"]
            )
        )  # type: ignore
        evaluation_data = self.validation_chart.data.values.to_dict()
        best_thresold_data = select_best_threshold(evaluation_data, min_precision)

        logger.info("Best eval stats :")
        logger.info(best_thresold_data)

        # Re-train on all data
        # Turning train df_pairs  into long format
        df_train = df_features_train.rename({"cluster_id": "cluster_id_true"})

        # preprocessing df_train
        df_train_preprocessed = self.preprocess_features(df_train)

        # Create training linker
        db_api_train = create_ducbdb_backend(Path("/Volumes/PRO-G40"))
        self.linker = Linker(
            df_train_preprocessed,  # type: ignore
            self.splink_settings,
            db_api_train,
        )
        # Train linker
        self.fit_linker()

        return self.linker, best_thresold_data

    def predict(
        self, threshold=0.5, build_waterfall_chart: bool = False
    ) -> tuple[pl.DataFrame, pl.DataFrame]:  # type: ignore[reportUnknownParameterType]
        """Run clustering and apply business rule filtering."""
        if self.linker is None:  # type: ignore[reportUnknownMemberType]
            raise RuntimeError(
                "BusinessRulesSplink must be fit() before calling predict()."
            )

        logger.info("[SPLINK] Generating predictions at threshold %.3f", threshold)
        # Generate pairwise predictions with Splink.
        df_predictions = self.linker.inference.predict()

        clusters = self.linker.clustering.cluster_pairwise_predictions_at_threshold(
            df_predictions, threshold_match_weight=threshold
        )

        result = (
            pl.DataFrame(df_predictions.as_pandas_dataframe()),
            pl.DataFrame(clusters.as_pandas_dataframe()),
        )
        if build_waterfall_chart:
            logger.info(
                "Building waterfall chart for predictions dataframe above threshold"
            )
            self.waterfall_chart_data = [
                e
                for e in df_predictions.as_record_dict()
                if e["match_weight"] >= threshold
            ]
            self.waterfall_chart = self.linker.visualisations.waterfall_chart(
                self.waterfall_chart_data, remove_sensitive_data=True
            )  # type: ignore

        return result

    def save(self, path: str):
        self.linker.misc.save_model_to_json(path)


def select_best_threshold(
    evaluation_data: list[dict], min_precision: float = 0.90
) -> dict:
    best_f_0_5 = 0
    best_f_0_5_index = 0

    for i, evaluation_dict in enumerate(evaluation_data):
        if evaluation_dict["precision"] >= min_precision:
            return evaluation_dict

        if evaluation_dict["f0_5"] > best_f_0_5:
            best_f_0_5_index = i

    logger.info("Precision aimed not reached, defaulting to best f0_5")
    return evaluation_data[best_f_0_5_index]
