# Splink model

An experimental record-linkage approach built on the
[`splink`](https://moj-analytical-services.github.io/splink/) probabilistic
linkage library, wrapped in `BusinessRulesSplink` to enforce domain business
rules on top of Splink's default settings.

> **Status**: experimental / alternative path. The current production path is
> the [XGBoost model](../xgboost/README.md).

## Pipeline

1. **Settings** (`training/splink/splink_config.py`) — map the shared
   `dedupe_variables_config` (mandatory / restricted / full) into Splink
   comparison and blocking rules. Blocking uses 2-digit code-postal prefix,
   strict SIREN match, and a 30 km geographic predicate.
2. **Model** (`splink_model.py`) — `BusinessRulesSplink` wraps Splink's
   `Linker` with a DuckDB backend (with the `spatial` extension) and applies
   business rules (same `source_id` / different `acteur_type_id`) both as
   blocking filters and as post-processing on candidate pairs.

## Training

Entry point: `python -m ml_deduplication.training.splink.training_pipeline_splink`

```
python -m ml_deduplication.training.splink.training_pipeline_splink \
    datasets/features_dataset_<date>.parquet
```

Splink uses supervised training on labeled pairs via its `Linker` API, with
blocking rules and threshold selection tuned for high precision (low false
positives).

## Inference

Entry point: `python -m ml_deduplication.inference.run_inference_splink`

```
python -m ml_deduplication.inference.run_inference_splink \
    --model-path <path> [--model-threshold 0.85] \
    --database-uri <uri> [--output-dir outputs] [--split-by-departement]
```

Reads acteurs from the database (`luis.acteurs_inference`), predicts candidate
pairs, and writes `inference_clusters_<run_id>.parquet` and
`inference_predictions_<run_id>.parquet`.

## Dependencies

Splink lives in the `training` dependency group (`uv sync --group training`).
