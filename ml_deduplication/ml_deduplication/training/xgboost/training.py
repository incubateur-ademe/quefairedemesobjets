import logging
from collections.abc import Sequence
from typing import Any

import numpy as np
import polars as pl
from ml_deduplication.modeling.xgboost.model import (
    XGBoostBusinessRulesModel,
)
from ml_deduplication.training.settings import PROJECT_FOLDER, RANDOM_SEED
from ml_deduplication.training.xgboost.preprocessing import prepare_folds
from ml_deduplication.training.xgboost.utils import (
    compute_pairwise_metrics_at_thresholds,
    generate_performance_reports,
)
from sentence_transformers import SentenceTransformer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    average_precision_score,
    brier_score_loss,
    roc_auc_score,
)
from tqdm import tqdm
from tqdm.contrib.logging import logging_redirect_tqdm

logger = logging.getLogger(__name__)


def fit_sigmoid_calibrator(
    df_predictions: pl.DataFrame,
) -> LogisticRegression:
    calibrator = LogisticRegression(
        random_state=RANDOM_SEED,
        max_iter=1000,
    )

    X = df_predictions.select("score_true").to_numpy()
    y = df_predictions["label"].to_numpy()

    calibrator.fit(X, y)

    return calibrator


def apply_calibrator(
    calibrator: LogisticRegression,
    df_predictions: pl.DataFrame,
) -> pl.DataFrame:
    calibrated_scores = calibrator.predict_proba(
        df_predictions.select("score_true").to_numpy()
    )[:, 1]

    return df_predictions.with_columns(
        pl.Series("score_true_calibrated", calibrated_scores)
    )


def tune_xgboost_hyperparameters(
    df_entities: pl.DataFrame,
    embedding_model: SentenceTransformer,
    base_hyperparameters: dict[str, Any],
    n_splits: int = 5,
    n_trials: int = 20,
    candidate_thresholds: Sequence[float] | None = None,
    random_seed: int = RANDOM_SEED,
) -> dict[str, Any]:
    """
    Randomized search over XGBoost hyperparameters.

    Each trial runs the existing K-fold validation pipeline.
    Feature preprocessing is cached by prepare_folds(), so the expensive
    embedding/blocking/feature-generation steps are not repeated.

    Returns:
        {
            "best_hyperparameters": ...,
            "best_score": ...,
            "search_results": ...,
            "best_cv_results": ...,
        }
    """

    rng = np.random.default_rng(random_seed)

    search_space = {
        "max_depth": [2, 3, 4, 5, 6, 7, 8, 9, 10],
        "learning_rate": [0.02, 0.03, 0.05, 0.07, 0.1, 0.15, 0.3],
        "min_child_weight": [1, 2, 3, 5, 8, 10, 15],
        "subsample": [0.6, 0.7, 0.8, 0.9, 1.0],
        "colsample_bytree": [0.3, 0.5, 0.7, 0.8, 0.9, 1.0],
        "gamma": [0.0, 0.1, 0.3, 0.5, 0.8, 1.0],
        "reg_alpha": [0.0, 0.001, 0.01, 0.1, 0.5, 1.0],
        "reg_lambda": [0.1, 0.5, 1.0, 2.0, 5.0, 10.0],
        "scale_pos_weight": [0.8, 0.9, 1.0, 1.1, 1.2, 2, 3],
    }

    folds = prepare_folds(
        df_entities,
        embedding_model,
        n_splits=n_splits,
        cache_data_dir=PROJECT_FOLDER / "cache_artifacts",
    )

    search_results = []

    best_score = -np.inf
    best_hyperparameters = None
    best_cv_results = None
    best_trial_index = None
    with logging_redirect_tqdm():
        for trial in tqdm(range(n_trials), desc="Tuning XGBoost", colour="BLUE"):
            trial_params = dict(base_hyperparameters)

            for parameter, values in search_space.items():
                trial_params[parameter] = values[rng.integers(0, len(values))]

            logger.info(
                "Starting XGBoost tuning trial %s/%s",
                trial + 1,
                n_trials,
            )
            logger.info("Trial parameters: %s", trial_params)

            cv_results = train_xgboost_with_kfold_validation(
                df_entities=None,
                folds=folds,
                xgb_hyperparameters=trial_params,
                embedding_model=embedding_model,
                n_splits=n_splits,
                candidate_thresholds=candidate_thresholds,
            )

            df_threshold_results = cv_results["clusterwise_threshold_selection_results"]

            summary = df_threshold_results.group_by("threshold").agg(
                pl.col("pairwise_precision").mean().alias("mean_pairwise_precision"),
                pl.col("pairwise_recall").mean().alias("mean_pairwise_recall"),
                pl.col("pairwise_f1").mean().alias("mean_pairwise_f1"),
                pl.col("bcubed_precision").mean().alias("mean_bcubed_precision"),
                pl.col("bcubed_precision").std().alias("std_bcubed_precision"),
                pl.col("bcubed_recall").mean().alias("mean_bcubed_recall"),
                pl.col("bcubed_f1").mean().alias("mean_bcubed_f1"),
                pl.col("ari").mean().alias("mean_ari"),
                pl.col("homogeneity").mean().alias("mean_homogeneity"),
            )

            # Use the same criterion as the threshold selection:
            # maximize B-Cubed precision first, then B-Cubed recall.
            best_trial_threshold = summary.sort(
                [
                    "mean_bcubed_precision",
                    "mean_bcubed_recall",
                ],
                descending=[True, True],
            ).head(1)

            trial_score = (
                best_trial_threshold["mean_bcubed_precision"].item()
                - 0.5 * best_trial_threshold["std_bcubed_precision"].item()
            )

            trial_threshold = best_trial_threshold["threshold"].item()

            result = {
                "trial": trial + 1,
                **trial_params,
                "score": trial_score,
                "best_threshold": trial_threshold,
                "mean_bcubed_precision": best_trial_threshold[
                    "mean_bcubed_precision"
                ].item(),
                "std_bcubed_precision": best_trial_threshold[
                    "std_bcubed_precision"
                ].item(),
                "mean_bcubed_recall": best_trial_threshold["mean_bcubed_recall"].item(),
                "mean_bcubed_f1": best_trial_threshold["mean_bcubed_f1"].item(),
                "mean_pairwise_precision": best_trial_threshold[
                    "mean_pairwise_precision"
                ].item(),
                "mean_pairwise_recall": best_trial_threshold[
                    "mean_pairwise_recall"
                ].item(),
                "mean_pairwise_f1": best_trial_threshold["mean_pairwise_f1"].item(),
                "mean_ari": best_trial_threshold["mean_ari"].item(),
                "mean_homogeneity": best_trial_threshold["mean_homogeneity"].item(),
            }

            search_results.append(result)

            logger.info(
                "Trial %s/%s: score=%.5f, threshold=%.3f, "
                "bcubed_precision=%.5f, bcubed_recall=%.5f",
                trial + 1,
                n_trials,
                result["score"],
                result["best_threshold"],
                result["mean_bcubed_precision"],
                result["mean_bcubed_recall"],
            )

            if trial_score > best_score:
                best_score = trial_score
                best_hyperparameters = trial_params
                best_cv_results = cv_results
                best_trial_index = trial + 1
                logger.info(
                    "New best XGBoost parameters found: score=%.5f",
                    best_score,
                )

    if best_hyperparameters is None:
        raise RuntimeError("XGBoost hyperparameter search failed.")

    df_search_results = pl.DataFrame(search_results)
    logger.info(
        "Best trial search results are\n%s",
        df_search_results.filter(pl.col("trial") == best_trial_index),
    )
    return {
        "best_hyperparameters": best_hyperparameters,
        "best_score": best_score,
        "search_results": df_search_results,
        "best_cv_results": best_cv_results,
    }


def train_xgboost_with_kfold_validation(
    df_entities: pl.DataFrame | None,
    xgb_hyperparameters: dict,
    embedding_model: SentenceTransformer,
    folds: list[dict] | None = None,
    n_splits: int = 5,
    candidate_thresholds: Sequence[float] | None = None,
) -> dict[str, Any]:
    """
    Select threshold using cluster-level evaluation on KFold validation folds.

    Returns:
        best_threshold
        DataFrame with threshold results
        list of best_iteration from each fold
    """

    if folds is None:
        folds = prepare_folds(
            df_entities,
            embedding_model,
            n_splits=n_splits,
            cache_data_dir=PROJECT_FOLDER / "cache_artifacts",
        )

    if candidate_thresholds is None:
        candidate_thresholds = np.arange(0.50, 1.00, 0.001)

    candidate_thresholds = sorted(
        {float(np.clip(t, 0.001, 0.999)) for t in candidate_thresholds}
    )

    logger.info("Candidate thresholds: %s", candidate_thresholds)

    best_iterations: list[int] = []

    dfs_predictions_oof = []
    for i, fold_number in enumerate(folds):
        # 1. train
        fold_model = XGBoostBusinessRulesModel(xgb_hyperparameters=xgb_hyperparameters)

        fold_model.train(
            (fold_number["X_train"], fold_number["y_train"]),
            (fold_number["X_dev"], fold_number["y_dev"]),
        )

        best_iterations.append(int(fold_model._classifier.best_iteration))

        # 2. predict
        df_predictions_dev = pl.concat(
            [
                fold_model.predict(fold_number["X_dev"]),
                fold_number["y_dev"],
            ],
            how="horizontal",
        )

        logger.info(
            "Fold %s, ROC-AUC : %s, AP: %s",
            i,
            roc_auc_score(
                df_predictions_dev["label"], df_predictions_dev["score_true"]
            ),
            average_precision_score(
                df_predictions_dev["label"], df_predictions_dev["score_true"]
            ),
        )

        dfs_predictions_oof.append(
            df_predictions_dev.with_columns(pl.lit(i).alias("fold"))
        )
        # 3. evaluate every threshold ON THIS FOLD

    df_predictions_oof_full: pl.DataFrame = pl.concat(
        dfs_predictions_oof, how="vertical"
    )

    # CALIBRATION
    calibrator = fit_sigmoid_calibrator(df_predictions_oof_full)
    df_calibrated_oof_predictions_full = apply_calibrator(
        calibrator,
        df_predictions_oof_full,
    )
    ## Evaluate calibration
    raw_brier = brier_score_loss(
        df_calibrated_oof_predictions_full["label"],
        df_calibrated_oof_predictions_full["score_true"],
    )

    calibrated_brier = brier_score_loss(
        df_calibrated_oof_predictions_full["label"],
        df_calibrated_oof_predictions_full["score_true_calibrated"],
    )

    logger.info(
        "Brier score before calibration: %s, AFTER: %s", raw_brier, calibrated_brier
    )

    stats_to_compute = [
        pl.len().alias("num_examples"),
        pl.col("score_true").mean().alias("score_true_mean"),
        pl.col("score_true").median().alias("score_true_median"),
        pl.col("score_true").std().alias("score_true_std"),
        pl.col("score_true_calibrated").mean().alias("score_true_calibrated_mean"),
        pl.col("score_true_calibrated").median().alias("score_true_calibrated_median"),
        pl.col("score_true_calibrated").std().alias("score_true_calibrated_std"),
        pl.col("label").sum().alias("num_examples_pos"),
        pl.col("score_true")
        .filter(pl.col("label"))
        .mean()
        .alias("pos_score_true_mean"),
        pl.col("score_true")
        .filter(pl.col("label"))
        .median()
        .alias("pos_score_true_median"),
        pl.col("score_true").filter(pl.col("label")).std().alias("pos_score_true_std"),
        pl.col("score_true_calibrated")
        .filter(pl.col("label"))
        .mean()
        .alias("pos_score_true_calibrated_mean"),
        pl.col("score_true_calibrated")
        .filter(pl.col("label"))
        .median()
        .alias("pos_score_true_calibrated_median"),
        pl.col("score_true_calibrated")
        .filter(pl.col("label"))
        .std()
        .alias("pos_score_true_calibrated_std"),
    ]
    df_predictions_stats = df_calibrated_oof_predictions_full.group_by("fold").agg(
        stats_to_compute
    )

    logger.info("Threshold selection on calibrated score")
    df_threshold_metrics = compute_pairwise_metrics_at_thresholds(
        df_calibrated_oof_predictions_full, candidate_thresholds
    )

    target_precision = 0.97
    min_recall = 0.80
    candidates = df_threshold_metrics.filter(
        (pl.col("precision") >= target_precision) & (pl.col("recall") >= min_recall)
    )
    if candidates.is_empty():
        logger.warning("No threshold reaches target precision=%s", target_precision)
        candidates = df_threshold_metrics

    candidate_thresholds = candidates.get_column("threshold").to_numpy()

    clustering_thresold_selection_result = []
    for threshold in candidate_thresholds:
        for fold_number, fold in enumerate(folds):
            fold_model = XGBoostBusinessRulesModel(xgb_hyperparameters)

            df_preds_fold = df_calibrated_oof_predictions_full.filter(
                pl.col("fold") == fold_number
            )
            df_entities_dev_fold = fold["df_entities_dev"]
            _, df_clusters_pred_fold = fold_model.cluster(
                df_preds_fold.with_columns(
                    pl.col("score_true_calibrated").alias("score_true")
                ),
                df_entities_dev_fold,
                threshold,
            )

            clustering_report_fold = generate_performance_reports(
                df_entities_true=df_entities_dev_fold,
                df_cluster_pred=df_clusters_pred_fold,
            )
            clustering_thresold_selection_result.append(
                {
                    "threshold": threshold,
                    "fold": fold_number,
                    **{
                        f"pairwise_{k}": v
                        for k, v in clustering_report_fold["pairwise"].items()
                    },
                    **{
                        f"bcubed_{k}": v
                        for k, v in clustering_report_fold["clusterwise"][
                            "bcubed_without_singletons"
                        ].items()
                    },
                    **clustering_report_fold["clusterwise"]["sklearn"],
                }
            )

    df_clusterwise_threshold_selection = pl.DataFrame(
        clustering_thresold_selection_result
    )
    df_clusterwise_threshold_selection_agg = (
        df_clusterwise_threshold_selection.group_by("threshold").agg(
            pl.selectors.contains("precision").mean().name.prefix("mean_"),
            pl.selectors.contains("precision").std().name.prefix("std_"),
            pl.selectors.contains("recall").mean().name.prefix("mean_"),
        )
    )

    df_clusterwise_threshold_selection_agg_filtered = (
        df_clusterwise_threshold_selection_agg.filter(
            pl.col("mean_bcubed_recall") >= min_recall
        )
    )

    if len(df_clusterwise_threshold_selection_agg_filtered) == 0:
        logger.warning(
            "No threshold meet recall criteria, fallback to best threshold without recall filtering"
        )
        best_threshold = (
            df_clusterwise_threshold_selection_agg.with_columns(
                (
                    pl.col("mean_bcubed_precision")
                    - 0.5 * pl.col("std_bcubed_precision")
                ).alias("score")
            )
            .sort(["score", "mean_bcubed_recall"], descending=[True, True])
            .head(1)["threshold"]
        )
    else:
        best_threshold = (
            df_clusterwise_threshold_selection_agg_filtered.with_columns(
                (
                    pl.col("mean_bcubed_precision")
                    - 0.5 * pl.col("std_bcubed_precision")
                ).alias("score")
            )
            .sort(["score", "mean_bcubed_recall"], descending=[True, True])
            .head(1)["threshold"]
        )

    logger.info("Selected cluster threshold: %.4f", best_threshold)
    logger.info(
        "Pairwise Threshold selection CV results:\n%s",
        df_threshold_metrics.sort(["threshold"], descending=[True]),
    )
    logger.info(
        "Clusterwise Threshold selection CV results:\n%s",
        df_clusterwise_threshold_selection.sort(
            ["threshold", "fold"], descending=[True, False]
        ),
    )

    cv_validation_results = {
        "best_threshold": best_threshold,
        "best_iterations": best_iterations,
        "oof_predictions_stats": df_predictions_stats,
        "clusterwise_threshold_selection_results": df_clusterwise_threshold_selection,
        "calibrator": calibrator,
    }
    return cv_validation_results
