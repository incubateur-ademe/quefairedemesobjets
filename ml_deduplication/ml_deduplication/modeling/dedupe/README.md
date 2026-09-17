# Dedupe model

The original entity-deduplication approach, built on the
[`dedupe`](https://github.com/dedupeio/dedupe) library. It is **not** the main
path anymore — it is retained for reference and comparison.

> **Status**: legacy / reference path. The current production path is the
> [XGBoost model](../xgboost/README.md). See also the [Splink path](../splink/README.md).

## Pipeline

1. **Features** (`training/dedupe/features.py`) — define the feature sets
   (`MANDATORY`, `RESTRICTED`, `FULL`) and per-field comparison variables
   (`exact`, `levenshtein`, etc.) consumed by `dedupe`.
2. **Blocking & model selection** (`training/dedupe/model_selection.py`) — build
   the hyperparameter grid (index predicates on/off, feature sets, variable
   configs) and select the best classification threshold.
3. **Model** (`modeling/dedupe/model.py`) — `BusinessRulesDedupe` extends
   `dedupe.Dedupe` with business rules:
   - `unique_fields` (e.g. `source_id`): same value → conflict.
   - `distinct_fields` (e.g. `acteur_type_id`): different value → conflict.
     Rules are enforced at the **blocking**, **scoring**, and **clustering**
     levels. `modeling/dedupe/xgb_model.py` provides `BusinessRulesXGBoost`, a
     variant using XGBoost as the internal classifier.

## Training

Entry point: `python -m ml_deduplication.training.dedupe.training_pipeline_dedupe`

```
python -m ml_deduplication.training.dedupe.training_pipeline_dedupe \
    datasets/features_dataset_<date>.parquet \
    [--mode simple|tuning] [--model-type dedupe|xgboost|splink]
```

- `--mode tuning` searches the hyperparameter grid (feature sets × index
  predicates) and picks the threshold maximizing precision subject to
  `min_recall=0.25` on the dev split.
- `--model-type` selects which model to train (`dedupe` by default; also
  accepts `xgboost` / `splink`).
- Outputs a saved model JSON and `training_results_*.json` in `--log-dir`.

## Inference

Entry point: `python -m ml_deduplication.inference.run_inference`

```
python -m ml_deduplication.inference.run_inference \
    --model-path <path> --model-type dedupe|xgboost \
    [--model-threshold 0.85] --database-uri <uri> [--output-dir outputs]
```

Reads acteurs from the database (`luis.acteurs_inference`), partitions per
department, and writes `inference_clusters_<run_id>.parquet` while also saving
the clusters back to the database (`luis.deduplication_clusters`).

## Dependencies

`dedupe` lives in the `training` dependency group
(`uv sync --group training`).
