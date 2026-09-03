"""Splink-based deduplication model with business rules support."""

import logging
from collections import defaultdict
from collections.abc import Hashable, Sequence
from itertools import combinations
from pathlib import Path
from statistics import mean

import duckdb
import polars as pl
from altair import Chart
from ml_deduplication.modeling.splink.schemas import SCHEMA_CLUSTERS, SCHEMA_PREDS
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
        df_embeddings: pl.DataFrame | None = None,
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
            df_features_preprocessed = self.preprocess_features(
                df_features, df_embeddings
            )

            self.linker = Linker(
                df_features_preprocessed,  # type: ignore
                self.splink_settings,
                db_api=db_api,
            )

        self._unique_fields = unique_fields
        self._distinct_fields = distinct_fields

        self.validation_chart: None | Chart = None
        self.waterfall_chart_data: None | list[dict] = None
        self.waterfall_chart: None | Chart = None

    def preprocess_features(
        self, df_features: pl.DataFrame, df_embeddings: pl.DataFrame | None = None
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

        if df_embeddings is None:
            addresses_tensors = self.embedding_model.encode(addresses_texts)

            df_vectors = pl.DataFrame({"adresse_clean_vector": addresses_tensors})
            df_features_preprocessed = pl.concat(
                [df_features_preprocessed, df_vectors], how="horizontal"
            )
        else:
            df_features_preprocessed = df_features_preprocessed.join(
                df_embeddings, on="entity_id", validate="1:1", how="left"
            )

        df_features_preprocessed = df_features_preprocessed.with_columns(
            pl.when(
                pl.col("adresse").is_null() & pl.col("adresse_complement").is_null()
            )
            .then(None)
            .otherwise(pl.col("adresse_clean_vector").cast(pl.Array(pl.Float32, 1024)))
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
        self,
        threshold=0.5,
        build_waterfall_chart: bool = False,
        materialize_outputs_as_parquet: bool = False,
        outputs_parquet_folder: Path | None = None,
        outputs_suffix: str | None = None,
    ) -> tuple[pl.DataFrame, pl.DataFrame] | None:  # type: ignore[reportUnknownParameterType]
        """Run clustering and apply business rule filtering."""
        if self.linker is None:  # type: ignore[reportUnknownMemberType]
            raise RuntimeError(
                "BusinessRulesSplink must be fit() before calling predict()."
            )

        logger.info("[SPLINK] Generating predictions at threshold %.3f", threshold)
        # Generate pairwise predictions with Splink.
        predictions = self.linker.inference.predict(threshold_match_weight=threshold)

        clusters = self.linker.clustering.cluster_pairwise_predictions_at_threshold(
            predictions, threshold_match_weight=threshold
        )

        if materialize_outputs_as_parquet:
            if outputs_parquet_folder is None:
                raise ValueError("outputs_parquet_folder must be provided.")
            predictions.to_parquet(
                str(outputs_parquet_folder / f"predictions_{outputs_suffix}.parquet"),
                overwrite=True,
            )
            clusters.to_parquet(
                str(outputs_parquet_folder / f"clusters_{outputs_suffix}.parquet"),
                overwrite=True,
            )
            return

        df_predictions = pl.DataFrame(
            predictions.as_record_dict(),
            schema_overrides=SCHEMA_PREDS,
        )
        df_clusters = pl.DataFrame(
            clusters.as_record_dict(),
            schema_overrides=SCHEMA_CLUSTERS,
        )

        # Apply business rules
        df_clusters_cleaned = df_clusters

        if build_waterfall_chart:
            logger.info(
                "Building waterfall chart for predictions dataframe above threshold"
            )
            self.waterfall_chart_data = [
                e
                for e in predictions.as_record_dict()
                if e["match_weight"] >= threshold
            ]
            self.waterfall_chart = self.linker.visualisations.waterfall_chart(
                self.waterfall_chart_data, remove_sensitive_data=True
            )  # type: ignore

        return df_predictions, df_clusters_cleaned

    def _has_conflict(
        self, entity_a: dict[str, object], entity_b: dict[str, object]
    ) -> bool:
        """Return True if two entities conflict on any field."""
        unique_conflicts = any(
            entity_a[field] is not None
            and entity_b[field] is not None
            and (entity_a[field] == entity_b[field])
            for field in self._unique_fields
        )

        distinct_conflicts_list = []
        for field in self._distinct_fields:
            if (entity_a[field] is None) or (entity_b[field] is None):
                distinct_conflicts_list.append(False)
                continue
            if (
                (field == "acteur_type_id")
                and ((int(entity_a[field]) == 3) and (int(entity_b[field]) == 4))
                or ((int(entity_a[field]) == 4) and (int(entity_b[field]) == 3))
            ):
                distinct_conflicts_list.append(False)
                continue
            distinct_conflicts_list.append(entity_a[field] != entity_b[field])
        distinct_conflicts = any(distinct_conflicts_list)

        return unique_conflicts or distinct_conflicts

    def _conflicts_in_cluster(
        self,
        cluster_ids: Sequence[Hashable],
        attributes: dict[str, dict[str, object]],
    ) -> dict[str, set]:
        """
        Pour chaque entité du cluster, retourne l'ensemble des autres entités
        avec lesquelles elle est en conflit selon les business rules.
        """
        conflicts = defaultdict(set)
        for id_a, id_b in combinations(cluster_ids, 2):
            attrs_a, attrs_b = attributes[id_a], attributes[id_b]
            if self._has_conflict(attrs_a, attrs_b):
                conflicts[id_a].add(id_b)
                conflicts[id_b].add(id_a)
        return conflicts

    def _resolve_cluster(
        self,
        entities_dicts: dict[str, dict],
    ) -> tuple[list[str], list[str]]:
        """
        Retire des entités d'un seul cluster jusqu'à ce qu'il respecte les
        règles métier. Retourne (ids_conservés, ids_retirés), ces derniers
        dans l'ordre où ils ont été retirés.
        """
        remaining = list(entities_dicts.keys())
        removed: list[str] = []

        while True:
            conflicts = self._conflicts_in_cluster(remaining, entities_dicts)
            if not conflicts:
                break
            # on retire l'entité la plus conflictuelle ; en cas d'égalité,
            # celle dont le score de confiance moyen est le plus faible
            worst = max(
                conflicts,
                key=lambda entity_id: (
                    len(conflicts[entity_id]),
                    -entities_dicts[entity_id]["mean_score"],
                ),
            )
            remaining.remove(worst)
            removed.append(worst)
        return remaining, removed

    def apply_business_rules(
        self, df_clusters: pl.DataFrame, df_predictions: pl.DataFrame
    ) -> pl.DataFrame:
        """
        Applique les règles métiers à la sortie de l'algorithme de clusterisation.
        """

        logger.debug(
            "Applying business rules to %s clusters",
            df_clusters.select(pl.col("cluster_id").n_unique()).item(),
        )
        clusters_dict = defaultdict(dict)
        for (_, cluster_id), df in df_clusters.filter(
            pl.col("entity_id").count().over("cluster_id") > 1
        ).group_by("cluster_id"):
            for row in df.iter_rows(named=True):
                entity_id = row["entity_id"]
                siblings_entities_ids = df.filter(pl.col("entity_id") != entity_id)[
                    "entity_id"
                ].to_list()

                scores = df_predictions.filter(
                    (
                        (pl.col("entity_id_l") == entity_id)
                        & (pl.col("entity_id_r").is_in(siblings_entities_ids))
                    )
                    | (
                        (pl.col("entity_id_r") == entity_id)
                        & (pl.col("entity_id_l").is_in(siblings_entities_ids))
                    )
                )["match_weight"].to_list()

                entity_dict = {**row, "mean_score": mean(scores)}
                clusters_dict[cluster_id][entity_id] = entity_dict

        entity_ids_to_remove = []
        for cluster_id, entities in clusters_dict.items():
            _, removed_ids = self._resolve_cluster(entities)
            entity_ids_to_remove.extend(removed_ids)

        df_clusters = df_clusters.with_columns(
            pl.when(pl.col("entity_id").is_in(entity_ids_to_remove))
            .then(pl.concat_str(pl.lit("c_singleton_business_rules_"), "entity_id"))
            .otherwise("cluster_id")
            .alias("cluster_id")
        )

        logger.debug(
            "New clusters count after business rules applied : %s",
            df_clusters.select(pl.col("cluster_id").n_unique()).item(),
        )
        return df_clusters

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
