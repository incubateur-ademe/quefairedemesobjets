# XGBoost model

This is the **current production path** for entity deduplication. It trains a
custom gradient-boosted classifier (`XGBoostBusinessRulesModel`) on engineered
candidate pairs, calibrates its scores, and clusters the results with
business-rule constraints.

## Pipeline

1. **Blocking** (`blocking.py`) — generate candidate pairs with DuckDB using
   three predicates (matching `siren`, same `code_postal` prefix, and a
   geographic grid within 30 km), then deduplicate the union. Business rules
   (same `source_id` / different `acteur_type_id` / same `parent_id`) filter
   conflicting pairs out during blocking.
2. **Feature engineering** (`features_engineering.py`) — compute pairwise
   similarity features (Jaro-Winkler on names/cities, SIRET/SIREN/telephone/
   code commune/code postal matches, address-embedding cosine distance, and
   geographic distance).
3. **Preprocessing** (`preprocessing.py`) — normalize strings, build address
   embeddings with `sentence-transformers` (`Lajavaness/sentence-camembert-large`),
   and assemble the training/prediction matrix.
4. **Model** (`model.py`) — an `XGBClassifier` trained on the pair features,
   followed by a logistic-regression **calibrator** (`apply_calibrator`) that
   maps raw scores to calibrated probabilities.
5. **Clustering** (`clustering.py`) — `ConstrainedUnionFind` connects pairs
   above a threshold while enforcing business rules.

## Training

Entry point: `python -m ml_deduplication.training.xgboost.training_pipeline_xgboost`

```
python -m ml_deduplication.training.xgboost.training_pipeline_xgboost \
    datasets/features_dataset_<date>.parquet [--mode tuning] [--n-trials 30]
```

- K-fold cross-validation selects the best cluster threshold and the number of
  boosting rounds (`n_estimators`).
- `--mode tuning` runs Optuna hyperparameter search over `n_trials`.
- Artifacts (in `logs/training_<mode>_<timestamp>/`): `model.json`,
  `calibrator.pkl`, `hyperparameters.json`, `training_results.json`, plus
  test-set predictions and clusters parquet files.

## Inference

Entry point: `python -m ml_deduplication.inference.xgboost.run_inference`

```
python -m ml_deduplication.inference.xgboost.run_inference \
    [--model-path <dir>] [--model-threshold 0.5] [--output-dir outputs] \
    [--split-by-departement] [--linkage-column _dataset] \
    <acteurs.parquet | --acteurs-table <table> --database-uri <uri>>
```

- Reads acteurs from a **file** (CSV/parquet) or a **database table/view**
  (`--acteurs-table` + `--database-uri`); exactly one source is required.
- `--linkage-column` enables cross-dataset entity linkage mode: only pairs
  across two datasets (e.g. `_dataset` values `A` vs `B`) are considered at the
  blocking stage.
- `--split-by-departement` processes each department separately to bound memory.
- Outputs `inference_clusters_<run_id>.parquet` and
  `inference_predictions_<run_id>.parquet` in `--output-dir`.

This is the model served by the Docker inference image
(`ml_deduplication/Dockerfile`) and the `Makefile` `build` / `run` / `buildx`
targets.

## Dependencies

Included in the base `[project].dependencies` (inference-only set): `polars`,
`duckdb`, `xgboost`, `scikit-learn`, `sentence-transformers`,
`polars-distance`, `pyarrow`, `connectorx` / `sqlalchemy` / `psycopg` (DB
reads). No extra `training`-group packages are required at inference time.
