import argparse
import json
import logging
from collections.abc import Sequence
from datetime import datetime, timezone
from pathlib import Path
from pickle import dump
from typing import Any

from sentence_transformers import SentenceTransformer  # isort: skip
import numpy as np
import polars as pl
from ml_deduplication.modeling.xgboost.model import (
    DEFAULT_SHOULD_BE_DIFFERENT_FIELDS,
    DEFAULT_SHOULD_BE_EQUAL_FIELDS,
    XGBoostBusinessRulesModel,
)
from ml_deduplication.modeling.xgboost.preprocessing import preprocess_entities_df
from ml_deduplication.training.settings import LOGS_FOLDER
from ml_deduplication.training.xgboost.training import (
    apply_calibrator,
    train_xgboost_with_kfold_validation,
    tune_xgboost_hyperparameters,
)
from ml_deduplication.training.xgboost.utils import (
    generate_performance_reports,
)
from sklearn.metrics import (
    classification_report,
)

logger = logging.getLogger(__name__)


def run_training_pipeline(
    df_features_entities: pl.DataFrame,
    hyperparameters: dict | None = None,
    n_splits: int = 5,
    candidate_thresholds: Sequence[float] | None = None,
    tune: bool = False,
    n_tuning_trials: int = 20,
) -> dict[str, Any]:
    df_entities_train = df_features_entities.filter(pl.col("split") == "train")
    df_entities_test = df_features_entities.filter(pl.col("split") == "test")

    embedding_model = SentenceTransformer(
        "Lajavaness/sentence-camembert-large",
    )

    if tune:
        logger.info(
            "Starting XGBoost hyperparameter tuning with %s trials",
            n_tuning_trials,
        )

        tuning_results = tune_xgboost_hyperparameters(
            df_entities=df_entities_train,
            embedding_model=embedding_model,
            base_hyperparameters=hyperparameters,
            n_splits=n_splits,
            n_trials=n_tuning_trials,
            candidate_thresholds=candidate_thresholds,
        )

        xgb_hyperparameters = tuning_results["best_hyperparameters"]

        logger.info(
            "Best XGBoost hyperparameters: %s",
            xgb_hyperparameters,
        )
        kfold_validation_results = tuning_results["best_cv_results"]

    else:
        xgb_hyperparameters = hyperparameters
        tuning_results = None

        if candidate_thresholds is None:
            candidate_thresholds = np.arange(0.05, 0.96, 0.05)

        kfold_validation_results = train_xgboost_with_kfold_validation(
            df_entities=df_entities_train,
            xgb_hyperparameters=xgb_hyperparameters,
            embedding_model=embedding_model,
            n_splits=n_splits,
        )

    best_threshold = kfold_validation_results["best_threshold"]
    best_iterations = kfold_validation_results["best_iterations"]
    calibrator = kfold_validation_results["calibrator"]
    df_threshold_cv_results = kfold_validation_results[
        "clusterwise_threshold_selection_results"
    ]

    logger.info("KFold best cluster threshold: %.4f", best_threshold)
    logger.info("KFold best iterations: %s", best_iterations)

    # Choose number of trees for final model.
    # Median is usually robust. Mean is also possible.
    final_n_estimators = int(np.median(best_iterations))

    logger.info(
        "Final model will be trained on all training data with n_estimators=%s",
        final_n_estimators,
    )

    final_hyperparameters = {
        **xgb_hyperparameters,
        "n_estimators": final_n_estimators,
    }

    final_model = XGBoostBusinessRulesModel(
        xgb_hyperparameters=final_hyperparameters,
    )

    # Final training without early stopping.
    X_train_full, y_train = preprocess_entities_df(
        df_entities_train,
        embedding_model=embedding_model,
        additional_columns_to_keep=[
            *DEFAULT_SHOULD_BE_DIFFERENT_FIELDS,
            *DEFAULT_SHOULD_BE_EQUAL_FIELDS,
        ],
    )
    final_model.train(train_data=(X_train_full, y_train))

    # Final evaluation on untouched test set.
    X_test, y_test = preprocess_entities_df(
        df_entities_test,
        embedding_model=embedding_model,
        additional_columns_to_keep=[
            *DEFAULT_SHOULD_BE_DIFFERENT_FIELDS,
            *DEFAULT_SHOULD_BE_EQUAL_FIELDS,
        ],
    )
    df_pairs_preds_test = final_model.predict(X_test)
    df_calibrated_pairs_preds_test = apply_calibrator(
        calibrator,
        df_pairs_preds_test,
    )
    test_classification_report_pairwise: dict = classification_report(
        y_test,
        df_calibrated_pairs_preds_test["score_true_calibrated"] >= best_threshold,
        output_dict=True,
    )  # type: ignore

    df_pairs_preds_test, df_pred_clusters_test = final_model.cluster(
        df_calibrated_pairs_preds_test.with_columns(
            pl.col("score_true_calibrated").alias("score_true")
        ),
        df_entities_test,
        threshold=best_threshold,
    )

    test_performance_reports = generate_performance_reports(
        df_entities_test,
        df_pred_clusters_test,
    )

    test_performance_reports = {
        **test_performance_reports,
        "pairwise_classification_report": test_classification_report_pairwise,
        "selected_cluster_threshold": final_model.best_threshold,
        "threshold_cv_results": df_threshold_cv_results.to_dicts(),
    }

    outputs = {
        "model": final_model,
        "calibrator": calibrator,
        "test_performace_report": test_performance_reports,
        "pairs_preds_test": df_pairs_preds_test,
        "pred_clusters_test": df_pred_clusters_test,
        "threshold_results": df_threshold_cv_results,
        "hyperparameters": xgb_hyperparameters,
    }

    return outputs


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments for the training pipeline."""
    parser = argparse.ArgumentParser(
        description="Run the ML deduplication training pipeline.",
    )

    parser.add_argument(
        "dataset_path",
        type=Path,
        help="Path to the features dataset parquet file.",
    )
    parser.add_argument(
        "--log-dir",
        type=Path,
        default=LOGS_FOLDER,
        help=f"Directory to save training results (default: {LOGS_FOLDER}).",
    )
    parser.add_argument(
        "--mode",
        choices=["simple", "tuning"],
        default="simple",
        help="Training mode: 'simple' for a single run, 'tuning' for hyperparameter tuning (default: simple).",
    )
    parser.add_argument(
        "--n-trials",
        type=int,
        default=30,
        help="Num trials for tuning, default 30",
    )
    parser.add_argument(
        "--n-splits",
        type=int,
        default=5,
        help="Num splits for CV, default to 5.",
    )

    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(filename)s | %(message)s",
        force=True,
    )
    # Validate dataset exists
    if not args.dataset_path.exists():
        logger.error("Dataset not found: %s", args.dataset_path)
        raise SystemExit(1)

    timestamp = datetime.now(timezone.utc).strftime("%Y_%m_%d_%H%M")
    # Ensure log directory exists
    log_dir: Path = args.log_dir / f"training_{args.mode}_{timestamp}"
    log_dir.mkdir(parents=True, exist_ok=True)

    logger.info("Loading features dataset at path %s", args.dataset_path)
    df_features = pl.read_parquet(args.dataset_path)

    hyperparameters = {
        "n_estimators": 1000,
        "max_depth": 5,
        "learning_rate": 0.02,
        "subsample": 0.7,
        "colsample_bytree": 0.9,
        "min_child_weight": 5,
        "gamma": 0.5,
        "reg_alpha": 1.0,
        "reg_lambda": 5.0,
        "scale_pos_weight": 0.9,
    }
    n_splits = args.n_splits
    if args.mode == "tuning":
        logger.info("Running hyperparameter tuning training")
        training_outputs = run_training_pipeline(
            df_features,
            hyperparameters=hyperparameters,
            tune=True,
            n_tuning_trials=args.n_trials,
            n_splits=n_splits,
        )
    else:
        logger.info("Running simple training with default parameters")

        training_outputs = run_training_pipeline(
            df_features, hyperparameters=hyperparameters, n_splits=n_splits
        )

    # save config:

    # Save model
    model = training_outputs["model"]
    if model is not None:
        model_save_dir = log_dir / "model.json"
        logger.info("Writing model at %s", model_save_dir)
        model.save(model_save_dir)

    hyperparameters = training_outputs["hyperparameters"]
    if hyperparameters is not None:
        hyperparameters_save_path = log_dir / "hyperparameters.json"
        with hyperparameters_save_path.open("w") as f:
            json.dump(hyperparameters, f)

    calibrator = training_outputs["calibrator"]
    if calibrator is not None:
        calibrator_save_dir = log_dir / "calibrator.pkl"
        logger.info("Writing calibrator at %s", calibrator_save_dir)
        with calibrator_save_dir.open("wb") as f:
            dump(calibrator, f, protocol=5)

    test_performance_reports = training_outputs["test_performace_report"]
    output_file = log_dir / "training_results.json"
    logger.info("Writing logs file at path %s", output_file)
    with output_file.open("w") as f:
        json.dump(test_performance_reports, f)

    df_pairs_preds_test = training_outputs["pairs_preds_test"]
    if df_pairs_preds_test is not None:
        output_df_preds_test_pred = log_dir / "training_test_pred_predictions.parquet"
        logger.info(
            "Writing df predictions test pred parquet file at path %s",
            output_df_preds_test_pred,
        )
        df_pairs_preds_test.write_parquet(output_df_preds_test_pred)

    df_preds_clusters_test = training_outputs["pred_clusters_test"]
    if df_preds_clusters_test is not None:
        output_df_clusters_test_pred = log_dir / "training_test_pred_clusters.parquet"
        logger.info(
            "Writing df clusters test pred parquet file at path %s",
            output_df_clusters_test_pred,
        )
        df_preds_clusters_test.write_parquet(output_df_clusters_test_pred)

    logger.info("Results saved to %s", output_file)
