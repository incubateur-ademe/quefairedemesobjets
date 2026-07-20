# ML Deduplication

Machine-learning based entity deduplication pipeline for actor records, built on top of the [`dedupe`](https://github.com/dedupeio/dedupe) library.

## Overview

This project provides a complete training and evaluation workflow to learn which pairs of entities (e.g., organizations / actors) refer to the same real-world object and cluster them accordingly. It follows an end-to-end pipeline:

- **Feature extraction** — build structured, comparable representations from raw records
- **Supervised learning** — train record linkage models on labeled match/distinct pairs
- **Hyperparameter tuning** — search over feature sets and model configurations with automatic threshold selection
- **Evaluation** — report both pair-wise (precision / recall / F1) and cluster-wise quality metrics against ground-truth clusters

## Project structure

```text
ml_deduplication/
├── main.py                     # Entry point to run the full pipeline locally
├── datasets/                   # Raw / prepared Parquet data
│   └── features_dataset_*.parquet
├── logs/                       # Training results (JSON) & artifacts
└── ml_deduplication/           # Package source
    ├── dataset/                # Data loading and feature engineering
    ├── evaluation/metrics/     # Pair-wise and cluster-wise quality metrics
    └── training/               # Model definitions, hyperparameter search & pipeline
        ├── model.py            # BusinessRulesDedupe wrapper around dedupe.Dedupe
        ├── model_selection.py  # Parameter grid generation + threshold selection
        ├── training_pipeline.py# run_training_with_hyperparameter_tuning()
        └── utils.py            # Helpers (entities dict, partition helpers…)
```

## Setup

Requires Python ≥ 3.13 and [`uv`](https://docs.astral.sh/uv/).

```bash
cd ml_deduplication
uv sync               # create .venv + install deps (polars, dedupe, …)
cp .env.example .env  # adapt local paths / credentials if any
```

## Usage

### Programmatic entry points

```python
from ml_deduplication.training.training_pipeline import (
    run_training_with_hyperparameter_tuning,
)
import polars as pl

df_features = pl.read_parquet("datasets/features_dataset_20260718.parquet")
model, results = run_training_with_hyperparameter_tuning(df_features)
```

## Key components

| Module                                      | What it does                                                                                                                   |
| ------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------ |
| `training/model.py` – `BusinessRulesDedupe` | Thin wrapper around `dedupe.Dedupe`; exposes `prepare_training()`, `train()` and `partition(data, threshold)`                  |
| `training/training_pipeline.py`             | Orchestrates a full pipeline: train on labeled pairs → pick best threshold (dev) → re-train → evaluate (test)                  |
| `training/model_selection.py`               | Builds the hyperparameter grid (feature combinations + index predicates) and searches for the optimal classification threshold |
| `evaluation/metrics/pairwise.py`            | Computes precision / recall / F1 at the pair level from ground-truth vs. predicted clusters                                    |
| `evaluation/metrics/cluster/`               | Cluster-level report: completeness, homogeneity, purity and size distributions                                                 |

## Evaluation metrics

- **Pair-wise** — treats every entity pair as a binary classification; reports precision, recall, F1. Used to select the best threshold on dev data (`min_recall=0.25`).
- **Cluster-wise** — assesses whole clusters (completeness, homogeneity) and size distributions vs. ground truth.

## Configuration & hyperparameters

The search grid lives in `training/model_selection.py`. It varies:

1. **Feature sets** — which columns are compared (names, addresses, SIRET, …).
2. **Dedupe field config** — per-field comparison rules (`exact`, `levenshtein` distance, etc.).
3. **Index predicates** — whether to build blocking indices for speed vs. exhaustiveness.

Run `uv run python main.py --help` (if implemented) or inspect `generate_parameter_grid()` to see current options.

## Datasets & logging

- Feature datasets live in `datasets/`. Expected columns include the entity identifier, ground-truth cluster id and a `split` column (`train` / `test`).
- Each tuning run appends a JSON summary under `logs/training_results_<date>.json`.

## Notes

- Training is **CPU-bound** (blocking + pairwise distance computation); large grids may take minutes to hours.
- The dedupe library's active-learning UI is intentionally bypassed — all training uses labelled pairs, which keeps the pipeline reproducible and CI-friendly.
