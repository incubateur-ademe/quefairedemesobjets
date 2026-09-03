import argparse
import json
import logging
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Literal

import numpy as np
import polars as pl
from joblib import Parallel, delayed
from ml_deduplication.evaluation.metrics.cluster import generate_full_cluster_report
from ml_deduplication.evaluation.metrics.pairwise import (
    pairwise_metrics_from_clusters,
    pairwise_metrics_from_scores,
)
from ml_deduplication.modeling.dedupe.model import (
    BusinessRulesDedupe,
)
from ml_deduplication.modeling.dedupe.xgb_model import BusinessRulesXGBoost
from ml_deduplication.training.dedupe.model_selection import (
    generate_parameter_grid,
    get_dedupe_variables_config,
    get_default_hyperparameters,
    select_best_threshold,
)
from ml_deduplication.training.utils import (
    build_entities_dict,
    create_acteur_to_cluster_dict,
    create_cluster_to_acteurs_dict,
    generate_pred_pairs_df,
    partition_to_dict,
    partition_to_results_dict,
    split_train_dev,
    stringify_params_list,
)
from tqdm import tqdm
from tqdm.contrib.logging import tqdm_logging_redirect

logging.basicConfig(
    level=logging.DEBUG, format="%(asctime)s | %(filename)s | %(message)s", force=True
)
logger = logging.getLogger(__name__)


LOGS_FOLDER = Path(__file__).parent.parent.parent / "logs"


def run_training_with_hyperparameter_tuning(
    df_features: pl.DataFrame,
    model_type: Literal["dedupe", "xgboost", "splink"] = "dedupe",
) -> tuple[Any | None, dict | None, pl.DataFrame | None]:
    param_grid = generate_parameter_grid(model_type)

    training_results = {"training_results": [], "best_results": {}}

    best_precision = 0
    best_metrics = None
    best_params = {}
    best_model = None
    best_df_pairs_test_pred = None
    start_time = time.time()

    with (
        tqdm_logging_redirect(),
        tqdm(
            param_grid, "Training model with hyperparameter tuning", colour="green"
        ) as t,
    ):
        for params in t:
            logger.info("Training with params : %s", params)
            model, results, df_pairs_test_pred = run_training_pipeline(
                df_features, params
            )
            logger.info("----" * 15)
            training_results["training_results"].append(
                {
                    "params": stringify_params_list(params),
                    "metrics": {
                        k: v for k, v in results.items() if k != "pred_clusters"
                    },
                }
            )
            if (
                training_precision := results["test_results"]["pairwise"]["precision"]
            ) > best_precision:
                best_precision = training_precision
                best_metrics = results
                best_params = params
                best_model = model
                best_df_pairs_test_pred = df_pairs_test_pred
                t.set_description(
                    f"Training model with hyperparameter tuning. Current best precision {best_precision}"
                )

    end_time = time.time()
    total_time = end_time - start_time
    logger.debug("Finished tuning in %ss", total_time)
    training_results["total_time_seconds"] = total_time
    training_results["best_results"] = {
        "metrics": best_metrics,
        "params": stringify_params_list(best_params),
    }
    logger.info(
        "Best metrics are %s",
        best_metrics,
    )
    logger.info(
        "Best params are %s",
        best_params,
    )

    return best_model, training_results, best_df_pairs_test_pred


def run_training_with_hyperparameter_tuning_parallel(
    df_features: pl.DataFrame,
    model_type: Literal["dedupe", "xgboost", "splink"],
    n_jobs: int = 8,
) -> tuple[Any | None, dict | None, pl.DataFrame | None]:

    param_grid = generate_parameter_grid(model_type)

    training_results = {
        "training_results": [],
        "best_results": {},
    }

    start_time = time.time()

    with (
        tqdm_logging_redirect(),
        tqdm(
            total=len(param_grid),
            desc="Training models",
            colour="green",
        ) as progress,
    ):
        results = []

        for result in Parallel(
            n_jobs=n_jobs,
            backend="loky",
            return_as="generator",
        )(
            delayed(run_training_pipeline)(
                df_features,
                params,
            )
            for params in param_grid
        ):
            progress.update(1)
            results.append(result)

    best_precision = 0
    best_model = None
    best_metrics = None
    best_params = None
    best_df_pairs_test_pred = None

    for params, (model, metrics, df_pairs_test_pred) in zip(
        param_grid,
        results,
    ):
        training_results["training_results"].append(
            {
                "params": stringify_params_list(params),
                "metrics": {k: v for k, v in metrics.items() if k != "pred_clusters"},
            }
        )

        precision = metrics["test_results"]["pairwise"]["precision"]

        if precision > best_precision:
            best_precision = precision
            best_model = model
            best_metrics = metrics
            best_params = params
            best_df_pairs_test_pred = df_pairs_test_pred

    total_time = time.time() - start_time

    training_results["total_time_seconds"] = total_time
    training_results["best_results"] = {
        "metrics": best_metrics,
        "params": stringify_params_list(best_params),
    }

    logger.info(
        "Finished tuning in %.2fs",
        total_time,
    )

    logger.info(
        "Best metrics: %s",
        best_metrics,
    )

    logger.info(
        "Best params: %s",
        best_params,
    )

    return (
        best_model,
        training_results,
        best_df_pairs_test_pred,
    )


def run_training_pipeline(
    df_features: pl.DataFrame, training_hyperparameters: dict
) -> tuple[Any, dict, pl.DataFrame]:

    results = {}

    model_type = training_hyperparameters.get("model_type", "dedupe")  # type: ignore[reportUnknownMemberType]

    # Create cluster to ids dict (for ground truth evaluation).
    cluster_to_acteur_dict = create_cluster_to_acteurs_dict(df_features)

    # Create id to cluster dict
    acteur_to_cluster_id_dict = create_acteur_to_cluster_dict(cluster_to_acteur_dict)

    # select features
    features_names = training_hyperparameters["features_names"]
    # Create entities dict
    entities_dict = build_entities_dict(df_features, features_names=features_names)

    # split train into train/dev
    df_train_sub, df_dev = split_train_dev(
        df_features.filter(pl.col("split") == "train"),
    )

    # config variables
    dedupe_variables_config = get_dedupe_variables_config(
        training_hyperparameters["dedupe_variables_config"]
    )

    model_type = training_hyperparameters.get("model_type", "dedupe")
    if model_type == "xgboost":
        logger.info("Starting XGB training")
        deduper = BusinessRulesXGBoost(
            variable_config=dedupe_variables_config,
            index_predicates=training_hyperparameters["index_predicates"],
        )
    else:
        logger.info("Starting dedupe training")
        deduper = BusinessRulesDedupe(
            variable_definition=dedupe_variables_config,
            index_predicates=training_hyperparameters["index_predicates"],
        )
    deduper.fit(
        df_train_sub,
        entities_dict,
    )
    logger.info("Finished training")

    # select threshold on dev
    logger.info("Starting best threshold selection....")
    entities_ids_dev = set(df_dev["identifiant_unique_i"].to_list()) | set(
        df_dev["identifiant_unique_j"].to_list()
    )
    entities_dict_dev = {
        k: v for k, v in entities_dict.items() if k in entities_ids_dev
    }
    id_to_cluster_id_dict_dev = {
        k: v for k, v in acteur_to_cluster_id_dict.items() if k in entities_ids_dev
    }
    best_threshold, best_metrics = select_best_threshold(
        deduper=deduper,
        entities_dev=entities_dict_dev,
        id_to_cluster_id_dev=id_to_cluster_id_dict_dev,
        min_recall=0.25,
        thresholds=np.concatenate(
            [np.arange(0.10, 0.91, 0.05), np.arange(0.91, 0.96, 0.01)]
        ),
    )
    logger.info(
        "Best threshold found: %s, best metrics: %s", best_threshold, best_metrics
    )

    results["model_selection"] = {
        "best_threshold": best_threshold,
        "best_metrics": best_metrics,
    }

    # train on full dataset (train+dev)
    if model_type == "xgboost":
        logger.info("Starting XGB training on full training set")
        deduper = BusinessRulesXGBoost(
            variable_config=dedupe_variables_config,
            index_predicates=training_hyperparameters["index_predicates"],
        )
    else:
        logger.info("Starting dedupe training on full training set")
        deduper = BusinessRulesDedupe(
            variable_definition=dedupe_variables_config,
            index_predicates=training_hyperparameters["index_predicates"],
        )
    deduper.fit(
        df_features.filter(pl.col("split") == "train"),
        entities_dict,
    )
    logger.info("Finished dedupe training on full training set")

    # evaluate on test with best threshold
    logger.info("Starting predicting on test set")
    df_test = df_features.filter(pl.col("split") == "test")
    entities_ids_test = set(df_test["identifiant_unique_i"].to_list()) | set(
        df_test["identifiant_unique_j"].to_list()
    )
    entities_dict_test = {
        k: v for k, v in entities_dict.items() if k in entities_ids_test
    }
    id_to_cluster_id_dict_test = {
        k: v for k, v in acteur_to_cluster_id_dict.items() if k in entities_ids_test
    }
    partition_test_pred, scores = deduper.partition(
        data=entities_dict_test, threshold=best_threshold, output_scores=True
    )

    # Pairwise score metrics
    df_test_scores = pl.DataFrame(scores).select(
        pl.col("pairs").arr.get(0).alias("identifiant_unique_i"),
        pl.col("pairs").arr.get(1).alias("identifiant_unique_j"),
        "score",
    )
    df_test_scores = df_test_scores.join(
        df_test.select(["identifiant_unique_i", "identifiant_unique_j", "label"]),
        on=["identifiant_unique_i", "identifiant_unique_j"],
    )
    scores_test = df_test_scores.get_column("score").to_numpy()
    y_test = df_test_scores.get_column("label").to_numpy().astype(int)

    test_score_metrics = pairwise_metrics_from_scores(scores_test, y_test)
    logger.info("Test pairwise score metrics: %s", test_score_metrics)

    # type: ignore
    id_to_cluster_test_pred = partition_to_dict(partition_test_pred)
    df_pairs_pred = generate_pred_pairs_df(partition_test_pred)

    pairwise_metrics = pairwise_metrics_from_clusters(
        id_to_cluster_id_dict_test, id_to_cluster_test_pred
    )
    logger.info("Test pairwise metrics: %s", pairwise_metrics)
    results["pred_clusters"] = partition_to_results_dict(partition_test_pred)

    clusterwise_metrics = generate_full_cluster_report(
        id_to_cluster_id_dict_test, id_to_cluster_test_pred
    )

    results["test_results"] = {
        "pairwise": {**pairwise_metrics, **test_score_metrics},
        "clusterwise": clusterwise_metrics,
    }

    return deduper, results, df_pairs_pred


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
        "--model-type",
        choices=["dedupe", "xgboost", "splink"],
        default=None,
        help="Type of model to use (default: None = dedupe)",
    )

    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()

    # Validate dataset exists
    if not args.dataset_path.exists():
        logger.error("Dataset not found: %s", args.dataset_path)
        raise SystemExit(1)

    # Ensure log directory exists
    args.log_dir.mkdir(parents=True, exist_ok=True)

    logger.info("Loading features dataset at path %s", args.dataset_path)
    df_features = pl.read_parquet(args.dataset_path)

    timestamp = datetime.now(timezone.utc).strftime("%Y_%m_%d_%H%M")

    if args.mode == "tuning":
        logger.info("Running hyperparameter tuning training")
        deduper, results, df_pairs_test_pred = run_training_with_hyperparameter_tuning(
            df_features,
            args.model_type,
        )
    else:
        logger.info("Running simple training with default parameters")
        default_params = get_default_hyperparameters(args.model_type)
        deduper, results, df_pairs_test_pred = run_training_pipeline(
            df_features, default_params
        )

    # Save model
    if deduper is not None:
        model_save_dir = args.log_dir / f"model_{args.mode}_{timestamp}.json"
        logger.info("Writing model at %s", model_save_dir)
        deduper.save(model_save_dir)

    output_file = args.log_dir / f"training_results_{args.mode}_{timestamp}.json"
    logger.info("Writing logs file at path %s", output_file)
    with output_file.open("w") as f:
        json.dump(results, f)

    if df_pairs_test_pred is not None:
        output_df_pairs_test_pred = (
            args.log_dir / f"training_{args.mode}_{timestamp}_test_pred_pairs.parquet"
        )
        logger.info(
            "Writing df pairs test pred parquet file at path %s",
            output_df_pairs_test_pred,
        )
        df_pairs_test_pred.write_parquet(output_df_pairs_test_pred)

    logger.info("Results saved to %s", output_file)
