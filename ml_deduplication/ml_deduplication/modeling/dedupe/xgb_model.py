"""Core XGBoost model for record deduplication, reusing dedupe's featurization."""

import base64
import json
import logging
import pickle
import tempfile
from pathlib import Path
from typing import Any, Self

import numpy as np
import polars as pl
from dedupe.blocking import Fingerprinter
from dedupe.datamodel import DataModel
from dedupe.labeler import DedupeDisagreementLearner
from ml_deduplication.modeling.dedupe.model import BusinessRulesMixin
from sklearn.base import clone
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import GroupKFold
from xgboost import XGBClassifier

logger = logging.getLogger(__name__)
RANDOM_SEED = 42


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

        self._platt_coef: float | None = None
        self._platt_intercept: float | None = None
        self.calibrator: LogisticRegression | None = None

    def _fit_calibrator(
        self,
        X: np.ndarray,
        y: np.ndarray,
        groups: np.ndarray,
        n_splits: int = 5,
    ) -> None:
        """
        Fit an isotonic calibrator using cluster-wise cross validation.
        """

        logger.info("Fitting probability calibrator (%d-fold GroupKFold)...", n_splits)

        gkf = GroupKFold(n_splits=n_splits)

        oof_scores = np.empty(len(y), dtype=np.float32)

        for train_idx, calib_idx in gkf.split(X, y, groups):
            model = clone(self.xgb_base)

            model.fit(
                X[train_idx],
                y[train_idx],
            )

            oof_scores[calib_idx] = model.predict_proba(X[calib_idx])[:, 1]

        self.calibrator = LogisticRegression(
            solver="lbfgs",
            C=1e10,  # almost no regularization
        )

        self.calibrator.fit(oof_scores.reshape(-1, 1), y)

        calibrated_scores = self.calibrator.predict_proba(oof_scores.reshape(-1, 1))[
            :, 1
        ]

        logger.info(
            "Calibration finished. Raw score mean %.3f -> calibrated %.3f.",
            oof_scores.mean(),
            calibrated_scores.mean(),
        )

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
                active_learner.matcher._classifier.set_params(
                    max_iter=1000, random_state=RANDOM_SEED
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

        logger.debug("Starting training XGBoost model")

        # Train calibrator
        groups = df_train["cluster_id_split"].cast(pl.String).to_numpy()

        self._fit_calibrator(
            X_cleaned,
            y,
            groups,
        )

        # Train base classifier on ALL data regardless.
        self.xgb_base.fit(X_cleaned, y)  # always trained on full dataset

        train_scores = self.xgb_base.predict_proba(X_cleaned)[:, 1]

        logger.debug("Training AUC: %s", roc_auc_score(y, train_scores))
        logger.debug("Training Positive mean: %s", train_scores[y == 1].mean())
        logger.debug("Training Negative mean: %s", train_scores[y == 0].mean())

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
        pairs_list = list(
            pairs_iterable
        )  # consume iterator once; re-iterate for records/features

        pair_records = []
        for (id_a, record_a), (id_b, record_b) in pairs_list:
            pair_records.append((record_a, record_b))

        if not pair_records:
            dtype = np.dtype([("pairs", object, 2), ("score", "f4")])
            return np.array([], dtype=dtype)

        # Compute features using dedupe's C-optimized distances() (same as LR!)
        X_distances = self.data_model.distances(pair_records)
        X_cleaned = np.nan_to_num(X_distances, nan=0.0).astype(np.float32)

        n_pairs = len(pairs_list)

        # No calibrator available — use base classifier probabilities directly.
        try:
            raw_scores = self.xgb_base.predict_proba(X_cleaned)[:, 1]

            if self.calibrator is not None:
                scores = self.calibrator.predict_proba(raw_scores.reshape(-1, 1))[:, 1]
            else:
                scores = raw_scores
        except Exception as e:
            logger.error("XGB prediction failed (%s)", e)
            raise

        if data is not None and (self._unique_fields or self._distinct_fields):
            num_conflicting_pairs = 0
            for i, pair in enumerate(pairs_list):
                id_a, id_b = pair[0][0], pair[1][0]
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
        ids_pairs = []
        for pair in pairs_list:
            ids_pairs.append((pair[0][0], pair[1][0]))
        scored_pairs["pairs"] = ids_pairs
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

        core = {
            "xgb_base": xgb_base_json,
            "calibrator": (
                base64.b64encode(pickle.dumps(self.calibrator)).decode("ascii")
                if self.calibrator is not None
                else None
            ),
        }

        var_config_json = (
            [_serialize_variable(v) for v in self.data_model.field_variables]
            if hasattr(self, "data_model")
            else []
        )  # type: ignore[attr-defined]

        learned_preds = getattr(getattr(self, "fingerprinter", None), "predicates", [])
        full_settings: dict[str, Any] = {
            "core": core,
            "variable_config_json": var_config_json,
            "business_rules": {
                "unique_fields": self._unique_fields,
                "distinct_fields": self._distinct_fields,
                "index_predicates": bool(self._index_predicates),
            },
            "predicates": (
                base64.b64encode(pickle.dumps(learned_preds)).decode("ascii")
                if learned_preds
                else None
            ),
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

    def __init__(
        self, settings_file: str | Path, variable_config: list[Any], num_cores: int = 1
    ):
        if hasattr(settings_file, "read"):
            full_settings = json.load(settings_file)
        else:
            with open(settings_file, "r", encoding="utf-8") as f:
                full_settings = json.load(f)

        # Load XGB model
        with tempfile.TemporaryDirectory() as tmpdirname:
            tmp_file_path = Path(tmpdirname) / "xgb_base.json"
            json.dump(full_settings["core"]["xgb_base"], tmp_file_path.open("w"))
            self.xgb_base = XGBClassifier()
            self.xgb_base.load_model(tmp_file_path)

        # Load calibrator
        encoded = full_settings["core"].get("calibrator")

        if encoded is None:
            self.calibrator = None
        else:
            self.calibrator = pickle.loads(base64.b64decode(encoded))

        business_rules = full_settings.get("business_rules", {})

        self._unique_fields = tuple(business_rules.get("unique_fields", ("source_id",)))
        self._distinct_fields = tuple(
            business_rules.get("distinct_fields", ("acteur_type_id",))
        )
        self._index_predicates = bool(business_rules.get("index_predicates", True))

        # Restore learned predicates from save, or fall back to defaults
        saved_preds_raw = full_settings.get("predicates")
        if saved_preds_raw:
            logger.debug("Loading saved predicates")
            _saved_predicates = pickle.loads(base64.b64decode(saved_preds_raw))
        else:
            _saved_predicates = None

        # Build fresh DataModel with working predicates
        self.data_model = DataModel(variable_config)

        if _saved_predicates is not None and self._index_predicates:
            raw_predicates = list(_saved_predicates)
        else:
            raw_predicates = []

        self.fingerprinter = Fingerprinter(raw_predicates)

    def score(self, pairs_iterable, data=None):
        """Score candidate pairs using loaded XGB on dedupe distances().

        Args:
            pairs_iterable: Iterator of ((id_a, record_a), (id_b, record_b)) tuples.
            data: Optional dict mapping entity_id -> {field_name: value}. When provided,
                  zero scores for conflicting pairs to match BusinessRulesMixin behavior.
        """
        pairs_list = list(pairs_iterable)
        pair_records = []
        for (id_a, record_a), (id_b, record_b) in pairs_list:
            pair_records.append((record_a, record_b))

        if not pair_records:
            dtype = np.dtype([("pairs", object, 2), ("score", "f4")])
            return np.array([], dtype=dtype)

        X_distances = self.data_model.distances(pair_records)
        X_cleaned = np.nan_to_num(X_distances, nan=0.0).astype(np.float32)
        n_pairs = len(pairs_list)

        try:
            raw_scores = self.xgb_base.predict_proba(X_cleaned)[:, 1]

            if self.calibrator is None:
                scores = raw_scores
            else:
                scores = self.calibrator.predict_proba(raw_scores.reshape(-1, 1))[:, 1]
        except AttributeError as exc:
            raise RuntimeError(
                "XGB base is unavailable. The loaded model may be corrupt.",
            ) from exc

        if data is not None and (self._unique_fields or self._distinct_fields):
            num_conflicting_pairs = 0
            for i, pair in enumerate(pairs_list):
                id_a, id_b = pair[0][0], pair[1][0]
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
        ids_pairs = []
        for pair in pairs_list:
            ids_pairs.append((pair[0][0], pair[1][0]))
        scored_pairs["pairs"] = ids_pairs
        scored_pairs["score"] = scores.astype(np.float32)
        return scored_pairs
