import argparse
import json
import logging
import time
from datetime import datetime
from pathlib import Path

import polars as pl
from tqdm import tqdm
from tqdm.contrib.logging import tqdm_logging_redirect

from ml_deduplication.evaluation.metrics.cluster import generate_full_cluster_report
from ml_deduplication.evaluation.metrics.pairwise import pairwise_metrics_from_clusters
from ml_deduplication.training.model import BusinessRulesDedupe
from ml_deduplication.training.model_selection import (
    generate_parameter_grid,
    select_best_threshold,
    get_default_hyperparameters,
)
from ml_deduplication.training.utils import (
    build_entities_dict,
    create_acteur_to_cluster_dict,
    create_cluster_to_acteurs_dict,
    partition_to_dict,
    partition_to_results_dict,
    split_train_dev,
    stringify_params_list,
    generate_pred_pairs_df,
)

logging.basicConfig(
    level=logging.DEBUG, format="%(asctime)s | %(filename)s | %(message)s"
)
logger = logging.getLogger(__name__)


LOGS_FOLDER = Path(__file__).parent.parent.parent / "logs"


def run_training_with_hyperparameter_tuning(
    df_features: pl.DataFrame,
) -> tuple[BusinessRulesDedupe | None, dict | None, pl.DataFrame | None]:
    param_grid = generate_parameter_grid()

    training_results = {"training_results": [], "best_results": {}}

    best_precision = 0
    best_metrics = None
    best_params = {}
    best_model = None
    best_df_pairs_test_pred = None
    start_time = time.time()

    with tqdm_logging_redirect():
        with tqdm(
            param_grid, "Training model with hyperparameter tuning", colour="green"
        ) as t:
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
                    training_precision := results["test_results"]["pairwise"][
                        "precision"
                    ]
                ) > best_precision:
                    best_precision = training_precision
                    best_metrics = results
                    best_params = params
                    best_model = model
                    best_df_pairs_test_pred = df_pairs_test_pred
                    t.set_description(
                        "Training model with hyperparameter tuning. Current best precision %s"
                        % best_precision
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


def run_training_pipeline(
    df_features: pl.DataFrame, training_hyperparameters: dict
) -> tuple[BusinessRulesDedupe, dict, pl.DataFrame]:

    results = {}

    # Create cluster to ids dict
    cluster_to_acteur_dict = create_cluster_to_acteurs_dict(df_features)

    # Create id to cluster dict
    acteur_to_cluster_id_dict = create_acteur_to_cluster_dict(cluster_to_acteur_dict)

    # select features
    features_names = training_hyperparameters["features_names"]
    # Create entities dict
    entities_dict = build_entities_dict(df_features, features_names=features_names)

    # split train into train/dev
    df_train_sub, df_dev = split_train_dev(
        df_features.filter(pl.col("split") == "train")
    )

    # config variables
    dedupe_variables_config = training_hyperparameters["dedupe_variables_config"]

    # train dedupe
    logger.info("Starting dedupe training")
    deduper = BusinessRulesDedupe(
        variable_definition=dedupe_variables_config,
        index_predicates=training_hyperparameters["index_predicates"],
    )
    deduper.fit(
        df_train_sub,
        entities_dict,
    )
    logger.info("Finished dedupe training")

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
    )
    logger.info(
        "Best threshold found: %s, best metrics: %s", best_threshold, best_metrics
    )

    results["model_selection"] = {
        "best_threshold": best_threshold,
        "best_metrics": best_metrics,
    }

    # train on full dataset (train+dev)
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
    partition_test_pred = deduper.partition(
        data=entities_dict_test, threshold=best_threshold
    )  # type: ignore
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
        "pairwise": pairwise_metrics,
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

    timestamp = datetime.now().strftime("%Y_%m_%d_%H%M")

    if args.mode == "tuning":
        logger.info("Running hyperparameter tuning training")
        deduper, results, df_pairs_test_pred = run_training_with_hyperparameter_tuning(
            df_features
        )
    else:
        logger.info("Running simple training with default parameters")
        default_params = get_default_hyperparameters()
        deduper, results, df_pairs_test_pred = run_training_pipeline(
            df_features, default_params
        )

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
