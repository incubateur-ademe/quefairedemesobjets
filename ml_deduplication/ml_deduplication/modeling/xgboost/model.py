import logging
from pathlib import Path
from typing import Self

import polars as pl
from ml_deduplication.modeling.xgboost.clustering import ConstrainedUnionFind
from xgboost import XGBClassifier
from xgboost.callback import EarlyStopping

logger = logging.getLogger(__name__)

DEFAULT_SHOULD_BE_DIFFERENT_FIELDS = ("source_id",)
DEFAULT_SHOULD_BE_EQUAL_FIELDS = ("acteur_type_id",)

FEATURES_COLUMNS_NAMES = (
    "nom_clean_dist",
    "adresse_clean_distance",
    "ville_clean_dist",
    "siren_match",
    "siret_match",
    "telephone_match",
    "code_commune_insee_match",
    "code_postal_match",
    "departement_match",
    "geo_distance",
    "acteur_type_id_l",
    "acteur_type_id_r",
)


class XGBoostBusinessRulesModel:
    def __init__(
        self,
        xgb_hyperparameters: dict,
        should_be_different_fields=DEFAULT_SHOULD_BE_DIFFERENT_FIELDS,
        should_be_equal_fields=DEFAULT_SHOULD_BE_EQUAL_FIELDS,
        n_jobs: int = 1,
    ):
        self.xgb_hyperparameters = xgb_hyperparameters

        self._should_be_different_fields = should_be_different_fields
        self._should_be_equal_fields = should_be_equal_fields
        self._feature_columns = FEATURES_COLUMNS_NAMES

        self._classifier = XGBClassifier(
            **xgb_hyperparameters,
            n_jobs=n_jobs,
            eval_metric="aucpr",
        )

        self.best_threshold: float | None = None
        self.best_validation_metrics: dict | None = None

    def train(
        self,
        train_data: tuple[pl.DataFrame, pl.DataFrame],
        dev_data: tuple[pl.DataFrame, pl.DataFrame] | None = None,
    ) -> Self:
        X_train, y_train = train_data
        if (
            len(missing_columns := (set(self._feature_columns) - set(X_train.columns)))
            > 0
        ):
            raise Exception(f"Missing columns in X_train dataset: {missing_columns}")

        eval_set = None
        if dev_data is not None:
            X_dev, y_dev = dev_data
            if (
                len(
                    missing_columns := (set(self._feature_columns) - set(X_dev.columns))
                )
                > 0
            ):
                raise Exception(
                    f"Missing columns in X_train dataset: {missing_columns}"
                )
            eval_set = [(X_dev.select(self._feature_columns), y_dev)]
            early_stop = EarlyStopping(
                rounds=20,
                metric_name="aucpr",
                data_name="validation_0",
                save_best=True,
            )
            self._classifier.set_params(callbacks=[early_stop])

        logger.info("Starting training classifier")
        self._classifier.fit(
            X_train.select(self._feature_columns),
            y_train,
            eval_set=eval_set,
            verbose=True,
        )

        if dev_data is not None:
            logger.info(
                "Finished training classifier, best iteration is %s with score %s",
                self._classifier.best_iteration,
                self._classifier.best_score,
            )

        return self

    def predict(self, X: pl.DataFrame) -> pl.DataFrame:
        if len(missing_columns := (set(self._feature_columns)) - set(X.columns)) > 0:
            raise Exception(f"Missing columns in X_train dataset: {missing_columns}")

        y_pred_scores = self._classifier.predict_proba(X.select(self._feature_columns))

        df_y_pred_scores = pl.DataFrame(
            y_pred_scores, schema=["score_false", "score_true"]
        )

        df_pairs_scores = pl.concat(
            [X, df_y_pred_scores],
            how="horizontal_extend",
        )

        return df_pairs_scores

    def _conflict_expr(self) -> pl.Expr:
        """Vectorized twin of _has_conflict, evaluated over the whole pairs df at once."""
        unique_conflict = (
            pl.any_horizontal(
                [
                    pl.col(f"{f}_l").is_not_null()
                    & pl.col(f"{f}_r").is_not_null()
                    & (pl.col(f"{f}_l") == pl.col(f"{f}_r"))
                    for f in self._should_be_different_fields
                ]
            )
            if self._should_be_different_fields
            else pl.lit(False)
        )

        def distinct_field_conflict(field: str) -> pl.Expr:
            both_null = pl.col(f"{field}_l").is_null() | pl.col(f"{field}_r").is_null()
            differ = pl.col(f"{field}_l") != pl.col(f"{field}_r")
            if field == "acteur_type_id":
                compatible_3_4 = (
                    (pl.col(f"{field}_l").cast(pl.Int64) == 3)
                    & (pl.col(f"{field}_r").cast(pl.Int64) == 4)
                ) | (
                    (pl.col(f"{field}_l").cast(pl.Int64) == 4)
                    & (pl.col(f"{field}_r").cast(pl.Int64) == 3)
                )
                return (
                    pl.when(both_null | compatible_3_4)
                    .then(pl.lit(False))
                    .otherwise(differ)
                )
            return pl.when(both_null).then(pl.lit(False)).otherwise(differ)

        distinct_conflict = (
            pl.any_horizontal(
                [distinct_field_conflict(f) for f in self._should_be_equal_fields]
            )
            if self._should_be_equal_fields
            else pl.lit(False)
        )

        return unique_conflict | distinct_conflict

    def cluster(
        self,
        df_pairs_scores: pl.DataFrame,
        df_entities: pl.DataFrame | None = None,
        threshold: float | None = None,
        max_null_pct: float | None = None,
    ) -> tuple[pl.DataFrame, pl.DataFrame]:
        logger.info("Starting constrained clustering entities")
        threshold = threshold if threshold is not None else self.best_threshold
        if threshold is None:
            raise ValueError(
                "No threshold available: pass one explicitly or train the model first."
            )

        n_features = len(self._feature_columns)
        df_pairs_scores_lazy = df_pairs_scores.lazy()

        df_pairs_scores_lazy = df_pairs_scores_lazy.with_columns(
            (
                pl.sum_horizontal(
                    [pl.col(c).is_null().cast(pl.Int32) for c in self._feature_columns]
                )
                / n_features
            ).alias("pct_null_features")
        )

        is_edge = (pl.col("score_true") >= threshold) & (~self._conflict_expr())
        if max_null_pct is not None:
            is_edge = is_edge & (pl.col("pct_null_features") <= max_null_pct)

        df_pairs_scores_lazy = df_pairs_scores_lazy.with_columns(
            is_edge.alias("is_edge")
        )
        df_pairs_final = df_pairs_scores_lazy.collect(engine="streaming")

        df_edges = df_pairs_final.filter(pl.col("is_edge"))

        if df_edges.is_empty():
            logger.warning("No edges passed the threshold and business rules.")
            return df_pairs_final, self._get_singletons(df_entities)

        # =====================================================================
        # Union-Find Contraint Dynamique
        # =====================================================================
        logger.info("Building entity attribute map for dynamic constraint checking...")

        # On extrait dynamiquement tous les champs à surveiller (avec suffixe _l et _r)
        fields_to_track = list(
            set(self._should_be_different_fields + self._should_be_equal_fields)
        )

        exprs_l = [pl.col("identifiant_unique_l").alias("entity_id")] + [
            pl.col(f"{f}_l").alias(f) for f in fields_to_track
        ]

        exprs_r = [pl.col("identifiant_unique_r").alias("entity_id")] + [
            pl.col(f"{f}_r").alias(f) for f in fields_to_track
        ]

        df_nodes_attrs = pl.concat(
            [
                df_edges.select(exprs_l),
                df_edges.select(exprs_r),
            ]
        ).unique(subset="entity_id")

        # Conversion en dictionnaire pour lookup O(1)
        entity_attributes = {
            row["entity_id"]: {f: row[f] for f in fields_to_track}
            for row in df_nodes_attrs.iter_rows(named=True)
        }

        logger.info(
            "Running Constrained Union-Find with rules: diff=%s, eq=%s",
            self._should_be_different_fields,
            self._should_be_equal_fields,
        )

        uf = ConstrainedUnionFind(
            entity_attributes=entity_attributes,
            should_be_different_fields=self._should_be_different_fields,
            should_be_equal_fields=self._should_be_equal_fields,
        )

        # Trier les arêtes par score décroissant pour privilégier les liens les plus forts
        edges_sorted = df_edges.sort("score_true", descending=True)
        col_l = edges_sorted["identifiant_unique_l"].to_list()
        col_r = edges_sorted["identifiant_unique_r"].to_list()

        for i in range(len(col_l)):
            uf.union(col_l[i], col_r[i])

        logger.info(
            "Constrained clustering finished. %s unions discarded to respect business rules",
            uf.refused_unions_count,
        )
        clusters_mapping = uf.get_clusters()

        df_entity_clusters = pl.DataFrame(
            {
                "entity_id": list(clusters_mapping.keys()),
                "cluster_id": list(clusters_mapping.values()),
            }
        )

        # Formater les IDs de cluster pour qu'ils soient uniques et lisibles
        unique_clusters = df_entity_clusters["cluster_id"].unique().to_list()
        cluster_id_map = {
            old_id: f"c_{new_id}" for new_id, old_id in enumerate(unique_clusters)
        }

        df_entity_clusters = df_entity_clusters.with_columns(
            pl.col("cluster_id").replace_strict(cluster_id_map).alias("cluster_id")
        )

        # Ajout des entités isolées (singletons)
        if df_entities is not None:
            df_entity_clusters = pl.concat(
                [
                    df_entity_clusters,
                    df_entities.filter(
                        pl.col("identifiant_unique")
                        .is_in(df_entity_clusters["entity_id"])
                        .not_()
                    )
                    .with_columns(
                        pl.format("c_singleton_{}", "identifiant_unique").alias(
                            "cluster_id"
                        )
                    )
                    .select(
                        pl.col("identifiant_unique").alias("entity_id"), "cluster_id"
                    ),
                ],
                how="vertical_relaxed",
            )

        return df_pairs_final, df_entity_clusters

    def _get_singletons(self, df_entities: pl.DataFrame) -> pl.DataFrame:
        if df_entities is None:
            return pl.DataFrame(
                schema={"entity_id": pl.String, "cluster_id": pl.String}
            )
        return df_entities.select(
            pl.col("identifiant_unique").alias("entity_id"),
            pl.format("c_singleton_{}", "identifiant_unique").alias("cluster_id"),
        )

    def save(self, path: Path):
        logger.debug("Saving xgb model to path: %s", path)
        self._classifier.save_model(path)
        logger.debug("Saved xgb model to path: %s", path)

    @classmethod
    def load(
        cls,
        xgb_model_path: Path,
        threshold: float | None = None,
        n_jobs: int = 1,
    ) -> Self:
        logger.debug("Loading xgb model from path: %s", xgb_model_path)

        if not xgb_model_path.exists():
            raise FileNotFoundError(f"XGBoost model not found: {xgb_model_path}")

        classifier = XGBClassifier(
            n_jobs=n_jobs,
            eval_metric="aucpr",
        )
        classifier.load_model(xgb_model_path)

        model = cls(
            xgb_hyperparameters={},
            n_jobs=n_jobs,
        )
        model._classifier = classifier
        model.best_threshold = threshold

        logger.debug(
            "Loaded xgb model from path: %s, threshold=%s",
            xgb_model_path,
            threshold,
        )

        return model
