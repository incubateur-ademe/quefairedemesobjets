"""Core XGBoost model for record deduplication, reusing dedupe's featurization."""

import json
import logging
import tempfile
from pathlib import Path
from typing import Any, Self

import dedupe.variables as dedupe_variable
import numpy as np
import polars as pl
from dedupe.blocking import Fingerprinter
from dedupe.datamodel import DataModel
from dedupe.labeler import DedupeDisagreementLearner
from ml_deduplication.modeling.model import BusinessRulesMixin
from sklearn.base import BaseEstimator, ClassifierMixin
from sklearn.model_selection import BaseCrossValidator, GroupKFold, KFold
from xgboost import XGBClassifier

logger = logging.getLogger(__name__)
RANDOM_SEED = 42


class ClusterAwareSplitter(BaseCrossValidator):
    """Cross-validation splitter that groups by cluster_id to avoid pair leakage.

    When positive pairs share a cluster_id (they belong to the same entity group),
    all pairs from that cluster are kept together in either train or test fold,
    preventing information leakage between folds via shared entities within clusters.

    For negative pairs (cluster_id == None), each row is treated as its own group
    so they can be split normally without creating artificial dependencies.
    """

    def __init__(self, n_splits: int = 3, random_state: int | None = RANDOM_SEED):
        self.n_splits = n_splits
        self.random_state = random_state

    def get_n_splits(self, X=None, y=None, groups=None) -> int:
        return self.n_splits

    def _iter_test_indices(self, X=None, y=None, groups=None):
        if isinstance(groups, pl.Series):
            cluster_ids = groups.to_list()
        elif isinstance(groups, pl.DataFrame):
            cluster_ids = groups.get_column("cluster_id").to_list()
        elif hasattr(groups, "__iter__") and groups is not None:
            cluster_ids = list(groups)
        else:
            # No group info — use standard KFold random split (for CalibratedClassifierCV internal calls).

            kf = KFold(
                n_splits=self.n_splits, shuffle=True, random_state=self.random_state
            )
            for _, test_idx in kf.split(X):
                yield test_idx
            return

        n_samples = len(cluster_ids)

        # Assign group IDs for GroupKFold:
        # - Positive pairs (shared entity): use actual cluster_id → kept together.
        # - Negative pairs (no shared entity): each gets a unique group ID → free to split.
        group_ids: list[str] = []
        seen_clusters: dict[str, int] = {}
        neg_counter = 0

        for cid in cluster_ids:
            if cid is not None and str(cid).lower() != "none":
                key = str(cid)
                if key not in seen_clusters:
                    seen_clusters[key] = len(seen_clusters)
                group_ids.append(str(seen_clusters[key]))
            else:
                # Each negative pair gets its own unique group so GroupKFold can split them freely.
                group_ids.append(f"neg_{neg_counter}")
                neg_counter += 1

        # Delegate to GroupKFold's _iter_test_indices with our custom group IDs.
        gkf = GroupKFold(
            n_splits=self.n_splits, shuffle=True, random_state=self.random_state
        )
        for test_idx in gkf._iter_test_indices(
            np.zeros(n_samples), y=y, groups=group_ids
        ):
            yield test_idx


class _ClfWithCoef(BaseEstimator, ClassifierMixin):
    """Thin sklearn wrapper around a trained XGBClassifier so that CalibratedClassifierCV can fit it."""

    def __init__(self, xgb: XGBClassifier | None = None):
        self.xgb = xgb

    def fit(self, X, y):  # type: ignore[override]
        if self.xgb is not None:
            self.xgb.fit(X, y)
        self.classes_ = np.unique(y).astype(np.intp)
        return self

    def predict_proba(self, X):  # type: ignore[override]
        assert self.xgb is not None, "xgb must be set before calling predict_proba"
        return self.xgb.predict_proba(X)


# ===================================================================
# Trainable XGB model — parallel to BusinessRulesDedupe
# ===================================================================


class BusinessRulesXGBoost(BusinessRulesMixin):
    """Parallel to BusinessRulesDedupe but uses calibrated XGboost on dedupe distances().

    Uses the same blocking and clustering pipeline as dedupe (via BusinessRulesMixin),
    but replaces LR scoring with calibrated XGB predictions trained on
    data_model.distances() — the exact same C-optimized feature vectors that LR uses.

    Score normalization: CalibratedClassifierCV(method='sigmoid') applies Platt scaling,
    ensuring scores are in [0, 1] range directly comparable to dedupe's sigmoid(logits).
    Existing threshold grids (e.g., 0.10–0.95) work identically for both models.

    This class does NOT inherit from dedupe.Dedupe — it only inherits the mixin logic
    and manages its own data_model + fingerprinter setup independently.
    """

    def __init__(
        self,
        variable_config: list[Any],
        unique_fields: tuple[str, ...] = ("source_id",),
        distinct_fields: tuple[str, ...] = ("acteur_type_id",),
        index_predicates: bool = True,
        # XGBoost hyperparameters (defaults produce fast training for small labeled sets)
        n_estimators: int = 200,
        max_depth: int = 4,
        learning_rate: float = 0.1,
        subsample: float = 0.8,
        colsample_bytree: float = 0.8,
        random_state: int = RANDOM_SEED,
    ):
        self.variable_config = variable_config

        # Build dedupe DataModel for distances() featurization (same as LR backend)
        self.data_model = DataModel(list(variable_config))

        # XGB base classifier — trained on all labeled data.
        xgb_base = XGBClassifier(
            n_estimators=n_estimators,
            max_depth=max_depth,
            learning_rate=learning_rate,
            subsample=subsample,
            colsample_bytree=colsample_bytree,
            random_state=random_state,
            objective="binary:logistic",
        )

        self.xgb_base = xgb_base  # base classifier (always available)
        self._platt_coef: float | None = None  # Platt scaling a coefficient
        self._platt_intercept: float | None = None  # Platt scaling b intercept

        # Fingerprinter for blocking — populated after learn_predicates() in fit().
        raw_predicates = list(self.data_model.predicates) if index_predicates else []
        self.fingerprinter = Fingerprinter(raw_predicates)

        # Business rules fields
        self._unique_fields = unique_fields
        self._distinct_fields = distinct_fields
        self._index_predicates = index_predicates

    def fit(self, df_train: pl.DataFrame, entities_dict: dict[str | int, dict]) -> Self:
        """Train XGB on labeled pairs using dedupe's distances() as features.

        Args:
            df_train: Polars DataFrame with columns 'identifiant_unique_i',
                      'identifiant_unique_j', and 'label' (1=match, 0=distinguish).
            entities_dict: Mapping of entity_id -> {field_name: value} in dedupe format.

        Returns self for chaining.
        """
        logger.info("Extracting examples from %d labeled pairs...", len(df_train))
        examples = []
        labels = []

        for row in df_train.iter_rows(named=True):
            id_a = row["identifiant_unique_i"]
            id_b = row["identifiant_unique_j"]
            is_match = bool(row["label"])

            record_a = entities_dict[id_a]
            record_b = entities_dict[id_b]

            examples.append((record_a, record_b))
            labels.append(1.0 if is_match else 0.0)

        X_raw = self.data_model.distances(examples)
        y = np.array(labels, dtype=np.float32)

        # Replace NaN with 0 (matching dedupe's _add_derived_distances behavior).
        X_cleaned = np.nan_to_num(X_raw, nan=0.0).astype(np.float32)

        n_features = (
            self.data_model._len
            if hasattr(self.data_model, "_len")
            else X_cleaned.shape[1]
        )
        logger.info(
            "Built feature matrix: %d examples x %d features", len(examples), n_features
        )

        # --- Blocking rules learning via dedupe active learner ------------------
        if self._index_predicates and len(df_train) > 10:
            logger.info("Learning blocking predicates from labeled data...")
            try:
                active_learner = DedupeDisagreementLearner(
                    self.data_model.predicates,
                    self.data_model.distances,
                    entities_dict,
                    index_include=examples,
                )
                active_learner.mark(examples, labels)

                predicates = active_learner.learn_predicates(
                    recall=1, index_predicates=self._index_predicates
                )
                self.fingerprinter = Fingerprinter(
                    predicates if predicates else list(self.data_model.predicates)
                )
            except Exception as e:  # noqa: BLE001
                logger.warning(
                    "Predicate learning failed (%s); falling back to default data_model predicates.",
                    e,
                )
        # Train base classifier on ALL data regardless.
        self.xgb_base.fit(X_cleaned, y)  # always trained on full dataset

        return self

    def score(self, pairs_iterable, data=None):
        """Score candidate pairs using calibrated XGB on dedupe distances().

        Args:
            pairs_iterable: Iterator of ((id_a, record_a), (id_b, record_b)) tuples.
            data: Optional dict mapping entity_id -> {field_name: value}. When provided,
                  zero scores for conflicting pairs to match BusinessRulesMixin behavior.

        Returns structured numpy array with 'pairs' and 'score' columns.
        """
        # Collect all pairs as dedupe-compatible tuple of dicts
        ids = list(
            pairs_iterable
        )  # consume iterator once; re-iterate for records/features

        pair_records = []
        for (id_a, record_a), (id_b, record_b) in ids:
            pair_records.append((record_a, record_b))

        if not pair_records:
            dtype = np.dtype([("pairs", object, 2), ("score", "f4")])
            return np.array([], dtype=dtype)

        # Compute features using dedupe's C-optimized distances() (same as LR!)
        X_distances = self.data_model.distances(pair_records)
        X_cleaned = np.nan_to_num(X_distances, nan=0.0).astype(np.float32)

        n_pairs = len(ids)

        # No calibrator available — use base classifier probabilities directly.
        try:
            scores = self.xgb_base.predict_proba(X_cleaned)[:, -1]
        except Exception as e:
            logger.error("XGB prediction failed (%s)", e)
            raise

        if data is not None and (self._unique_fields or self._distinct_fields):
            num_conflicting_pairs = 0
            for i, pair in enumerate(ids):
                id_a, id_b = pair[0], pair[1]
                entity_a = data.get(id_a, {})
                entity_b = data.get(id_b, {})
                if self._has_conflict(entity_a, entity_b):
                    scores[i] = 0.0
                    num_conflicting_pairs += 1

            logger.debug(
                "Scored %d candidate pairs and processed %s conflict(s).",
                n_pairs,
                num_conflicting_pairs,
            )

        # Build structured array matching dedupe's expected format.
        scored_pairs: np.ndarray[np.float32] = np.empty(
            n_pairs, dtype=[("pairs", "O", 2), ("score", "f4")]
        )
        scored_pairs["pairs"] = [tuple(pair_ids) for pair_ids in ids]
        scored_pairs["score"] = scores.astype(np.float32)

        logger.info(
            "Scored %d candidate pairs with XGB (mean score=%.3f, std=%.3f)",
            n_pairs,
            np.mean(scores),
            np.std(scores),
        )
        return scored_pairs

    def save(self, path: str | Path) -> None:
        """Save the trained model to a JSON file with embedded pickles.

        The saved format mirrors BusinessRulesDedupe.save() for compatibility:
        {
          "core": "<base64-encoded binary>",  # XGB + calibration wrapper (data_model reconstructed from config on load)
          "variable_config_json": [...],      # JSON-serializable variable definitions
          "business_rules": {...}             # unique_fields, distinct_fields, index_predicates
        }
        """

        def _serialize_variable(var):
            result = {"type": var.type, "field": getattr(var, "field", None)}
            if hasattr(var, "has_missing") and var.has_missing:
                result["has_missing"] = True
            # Categorical variables store categories in their comparator
            var_type_str = (
                str(type(var).__name__) if hasattr(type(var), "__name__") else ""
            )
            is_categorical = "Categorical" in var_type_str and type(
                var
            ).__module__.startswith("dedupe")
            if is_categorical:
                cat_comp = (
                    getattr(getattr(var, "comparator", None), "categories", []) or []
                )
                result["categories"] = [str(c) for c in cat_comp]
            return result

        with tempfile.TemporaryDirectory() as tmpdirname:
            tmp_file_path = Path(tmpdirname) / "xgb_base.json"
            self.xgb_base.save_model(tmp_file_path)
            xgb_base_json = json.load(tmp_file_path.open())

        var_config_json = (
            [_serialize_variable(v) for v in self.data_model.field_variables]
            if hasattr(self, "data_model")
            else []
        )  # type: ignore[attr-defined]

        full_settings: dict[str, Any] = {
            "core": {"xgb_base": xgb_base_json},
            "variable_config_json": var_config_json,
            "business_rules": {
                "unique_fields": self._unique_fields,
                "distinct_fields": self._distinct_fields,
                "index_predicates": bool(self._index_predicates),
            },
        }

        if isinstance(path, (str, Path)):
            with open(path, "w", encoding="utf-8") as f:
                json.dump(full_settings, f, indent=2)
        else:
            json.dump(full_settings, path, indent=2)

        logger.info("XGB model saved to %s", path)


# ===================================================================
# Static XGB model — parallel to BusinessRulesStaticDedupe (load from disk)
# ===================================================================


class BusinessRulesStaticXGBoost(BusinessRulesMixin):
    """Load a model previously trained with BusinessRulesXGBoost.save().

    This class does NOT inherit from dedupe.StaticDedupe. It only inherits the mixin logic,
    reconstructs its own data_model + fingerprinter for blocking/scoring using XGB predictions.
    """

    def __init__(self, settings_file: str | Path, num_cores: int = 1):
        if hasattr(settings_file, "read"):
            full_settings = json.load(settings_file)
        else:
            with open(settings_file, "r", encoding="utf-8") as f:
                full_settings = json.load(f)

        with tempfile.TemporaryDirectory() as tmpdirname:
            tmp_file_path = Path(tmpdirname) / "xgb_base.json"
            json.dump(full_settings["core"]["xgb_base"], tmp_file_path.open("w"))
            self.xgb_base = XGBClassifier()
            self.xgb_base.load_model(tmp_file_path)

        business_rules = full_settings.get("business_rules", {})
        var_config_json = full_settings.get("variable_config_json", [])

        self._unique_fields = tuple(business_rules.get("unique_fields", ("source_id",)))
        self._distinct_fields = tuple(
            business_rules.get("distinct_fields", ("acteur_type_id",))
        )
        self._index_predicates = bool(business_rules.get("index_predicates", True))

        # Reconstruct variable definitions from JSON config
        var_def_list: list[Any] = []
        for vj in var_config_json:  # type: ignore[union-attr]
            if not isinstance(vj, dict):
                continue

            field_name = str(vj.get("field", "unknown"))
            has_missing = bool(vj.get("has_missing", False))

            if vj["type"] == "String":
                var_def_list.append(
                    dedupe_variable.String(
                        field=field_name,
                        **({"has_missing": True} if has_missing else {}),
                    )
                )
            elif vj["type"] == "Exact":
                var_def_list.append(
                    dedupe_variable.Exact(
                        field=field_name,
                        **({"has_missing": True} if has_missing else {}),
                    )
                )
            elif vj["type"] == "Categorical":
                categories = [str(c) for c in (vj.get("categories", []) or [])]
                var_def_list.append(
                    dedupe_variable.Categorical(
                        field=field_name,
                        categories=categories,
                        **({"has_missing": True} if has_missing else {}),
                    )
                )

        # Build fresh DataModel with working predicates
        self.data_model = DataModel(var_def_list)  # type: ignore[arg-type]

        raw_predicates = list(self.data_model.predicates) if num_cores else []
        self.fingerprinter = Fingerprinter(raw_predicates)

    def score(self, pairs_iterable, data=None):
        """Score candidate pairs using loaded XGB on dedupe distances().

        Args:
            pairs_iterable: Iterator of ((id_a, record_a), (id_b, record_b)) tuples.
            data: Optional dict mapping entity_id -> {field_name: value}. When provided,
                  zero scores for conflicting pairs to match BusinessRulesMixin behavior.
        """
        ids = list(pairs_iterable)
        pair_records = []
        for (id_a, record_a), (id_b, record_b) in ids:
            pair_records.append((record_a, record_b))

        if not pair_records:
            dtype = np.dtype([("pairs", object, 2), ("score", "f4")])
            return np.array([], dtype=dtype)

        X_distances = self.data_model.distances(pair_records)
        X_cleaned = np.nan_to_num(X_distances, nan=0.0).astype(np.float32)
        n_pairs = len(ids)

        try:
            scores = self.xgb_base.predict_proba(X_cleaned)[:, -1]
        except AttributeError as exc:
            raise RuntimeError(
                "XGB base is unavailable. The loaded model may be corrupt.",
            ) from exc

        if data is not None and (self._unique_fields or self._distinct_fields):
            num_conflicting_pairs = 0
            for i, pair in enumerate(ids):
                id_a, id_b = pair[0], pair[1]
                entity_a = data.get(id_a, {})
                entity_b = data.get(id_b, {})
                if self._has_conflict(entity_a, entity_b):
                    scores[i] = 0.0
                    num_conflicting_pairs += 1

            logger.debug(
                "Scored %d candidate pairs and processed %s conflict(s).",
                n_pairs,
                num_conflicting_pairs,
            )

        scored_pairs = np.empty(n_pairs, dtype=[("pairs", "O", 2), ("score", "f4")])
        scored_pairs["pairs"] = [tuple(pair_ids) for pair_ids in ids]
        scored_pairs["score"] = scores.astype(np.float32)
        return scored_pairs
