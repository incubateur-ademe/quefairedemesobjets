import logging
from pathlib import Path
from typing import Self

import numpy as np
import polars as pl
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components
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

        self._unique_fields = should_be_different_fields
        self._distinct_fields = should_be_equal_fields
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
                    for f in self._unique_fields
                ]
            )
            if self._unique_fields
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
                [distinct_field_conflict(f) for f in self._distinct_fields]
            )
            if self._distinct_fields
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
        """
        Build entity clusters (connected components) from scored candidate pairs.

        Expects df_pairs_scores to have: identifiant_unique_l, identifiant_unique_r, score_true,
        the model's feature columns, and {field}_a / {field}_b for every field
        in self._unique_fields / self._distinct_fields (see predict()).

        threshold: score_true cutoff for an edge. Defaults to self.best_threshold.
        max_null_pct: if set, pairs with a higher fraction of null features than
            this are also excluded from edge formation (in addition to being
            flagged via pct_null_features for a downstream QA pass).

        Returns:
          - df_pairs_scores with two extra columns: pct_null_features, is_edge
          - df_entity_clusters: one row per entity_id with its cluster_id
        """
        logger.info("Starting clustering entities")
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

        # Node index, vectorized (no python-level dict/loop, scales to millions of rows)
        df_nodes = (
            pl.concat(
                [
                    df_pairs_scores_lazy.select(
                        pl.col("identifiant_unique_l").alias("entity_id")
                    ),
                    df_pairs_scores_lazy.select(
                        pl.col("identifiant_unique_r").alias("entity_id")
                    ),
                ]
            )
            .unique(subset="entity_id")
            .with_row_index("node_idx")
            .collect(engine="streaming")
        )
        n_nodes = df_nodes.height

        df_edges_idx = (
            df_pairs_scores_lazy.filter(pl.col("is_edge"))
            .select("identifiant_unique_l", "identifiant_unique_r")
            .join(
                df_nodes.lazy().rename(
                    {
                        "entity_id": "identifiant_unique_l",
                        "node_idx": "node_idx_a",
                    }
                ),
                on="identifiant_unique_l",
            )
            .join(
                df_nodes.lazy().rename(
                    {
                        "entity_id": "identifiant_unique_r",
                        "node_idx": "node_idx_b",
                    }
                ),
                on="identifiant_unique_r",
            )
        ).collect(engine="streaming")

        row = df_edges_idx.get_column("node_idx_a").to_numpy()
        col = df_edges_idx.get_column("node_idx_b").to_numpy()
        data = np.ones(len(row), dtype=np.int8)

        adjacency = coo_matrix((data, (row, col)), shape=(n_nodes, n_nodes))
        logger.debug("Starting connected components...")
        _, labels = connected_components(adjacency, directed=False)
        logger.debug("Finished connected components.")

        df_entity_clusters = df_nodes.with_columns(
            pl.Series("cluster_id", labels)
        ).select("entity_id", "cluster_id")

        # Adds entities that have been filtered out by the blocking step
        if df_entities is not None:
            df_entity_clusters = pl.concat(
                [
                    df_entity_clusters.with_columns(
                        "entity_id",
                        pl.format("c_pred_{}", "cluster_id").alias("cluster_id"),
                    ),
                    df_entities.filter(
                        pl.col("identifiant_unique")
                        .is_in(df_entity_clusters.get_column("entity_id").to_list())
                        .not_()
                    )
                    .with_columns(
                        pl.format("c_singleton_pred_{}", "identifiant_unique").alias(
                            "cluster_id"
                        )
                    )
                    .select(
                        pl.col("identifiant_unique").alias("entity_id"), "cluster_id"
                    ),
                ],
                how="vertical",
            )

        return (
            df_pairs_scores_lazy.collect(engine="streaming"),
            df_entity_clusters,
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
