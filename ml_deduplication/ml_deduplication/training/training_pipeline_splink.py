import argparse
import json
import logging
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Literal

import polars as pl
from altair import Chart
from sentence_transformers import SentenceTransformer
from tqdm import tqdm
from tqdm.contrib.logging import tqdm_logging_redirect

from ml_deduplication.evaluation.metrics.cluster import generate_full_cluster_report
from ml_deduplication.evaluation.metrics.pairwise import (
    pairwise_metrics_from_clusters,
)
from ml_deduplication.modeling.splink_model import (
    BusinessRulesSplink,
    create_ducbdb_backend,
)
from ml_deduplication.training.model_selection import (
    generate_parameter_grid,
)
from ml_deduplication.training.splink_config import SPLINK_SETTINGS
from ml_deduplication.training.utils import (
    create_acteur_to_cluster_dict,
    splink_cluster_df_to_dict,
    stringify_params_list,
)

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


def generate_test_reports(
    df_test: pl.DataFrame, df_clusters_test: pl.DataFrame
) -> dict:
    cluster_to_acteur_dict_test = {
        e["cluster_id_split"]: e["entity_id"]
        for e in df_test.group_by("cluster_id_split").agg("entity_id").to_dicts()
    }
    acteur_to_cluster_id_dict_test = create_acteur_to_cluster_dict(
        cluster_to_acteur_dict_test
    )
    id_to_cluster_test_pred = splink_cluster_df_to_dict(df_clusters_test)

    test_score_metrics = pairwise_metrics_from_clusters(
        acteur_to_cluster_id_dict_test, id_to_cluster_test_pred
    )
    logger.info("Test pairwise score metrics: %s", test_score_metrics)

    clusterwise_metrics = generate_full_cluster_report(
        acteur_to_cluster_id_dict_test, id_to_cluster_test_pred
    )

    return {
        "pairwise": {**test_score_metrics},
        "clusterwise": clusterwise_metrics,
    }


def run_training_pipeline(
    df_features: pl.DataFrame,
) -> tuple[
    BusinessRulesSplink,
    dict,
    pl.DataFrame,
    pl.DataFrame,
    list[dict] | None,
    Chart | None,
]:

    df_features = df_features.rename({"identifiant_unique": "entity_id"})
    results = {}
    splink_config = SPLINK_SETTINGS
    embedding_model = SentenceTransformer("Lajavaness/sentence-camembert-large")
    model = BusinessRulesSplink(
        splink_settings=splink_config, embedding_model=embedding_model
    )

    logger.info("Starting training on train set")
    df_train = df_features.filter(pl.col("split") == "train")
    linker, best_dev_data = model.train(df_train, min_precision=0.99)

    best_weight_threshold = best_dev_data["truth_threshold"]
    logger.info("Best weight threshold found :%s.", best_weight_threshold)
    logger.info("Best dev metrics: %s", best_dev_data)

    results["model_selection"] = {
        "best_threshold": best_weight_threshold,
        "best_metrics": best_dev_data,
    }

    # evaluate on test with best threshold
    logger.info("Starting predicting on test set")
    df_test = df_features.filter(pl.col("split") == "test")

    model_test = BusinessRulesSplink(
        linker.misc.save_model_to_json(),
        embedding_model,
        df_features=df_test,
        db_api=create_ducbdb_backend(Path("/Volumes/PRO-G40")),
    )

    df_predictions_test, df_clusters_test = model_test.predict(
        threshold=best_weight_threshold, build_waterfall_chart=True
    )

    performance_reports = generate_test_reports(df_test, df_clusters_test)
    logger.info("Test pairwise score metrics: %s", performance_reports["pairwise"])

    results["test_results"] = performance_reports

    return (
        model,
        results,
        df_predictions_test,
        df_clusters_test,
        model_test.waterfall_chart_data,
        model_test.waterfall_chart,
    )


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

    timestamp = datetime.now(timezone.utc).strftime("%Y_%m_%d_%H%M")
    # Ensure log directory exists
    log_dir: Path = args.log_dir / f"training_{args.mode}_{timestamp}"
    log_dir.mkdir(parents=True, exist_ok=True)

    logger.info("Loading features dataset at path %s", args.dataset_path)
    df_features = pl.read_parquet(args.dataset_path)

    if args.mode == "tuning":
        logger.info("Running hyperparameter tuning training")
        model, results, df_pred_test = run_training_with_hyperparameter_tuning(
            df_features,
            args.model_type,
        )
    else:
        logger.info("Running simple training with default parameters")
        (
            model,
            results,
            df_pred_test,
            df_clusters_test,
            test_waterfall_chart_data,
            test_waterfall_chart,
        ) = run_training_pipeline(df_features)

    # Save model
    if model is not None:
        model_save_dir = log_dir / f"model_{args.mode}_{timestamp}.json"
        logger.info("Writing model at %s", model_save_dir)
        model.save(str(model_save_dir.absolute()))

        logger.info("Writing model artifacts")
        charts_config = [
            {
                "chart_name": "match_weight_chart",
                "chart": model.linker.visualisations.match_weights_chart(),
            },
            {
                "chart_name": "m_u_parameters_chart",
                "chart": model.linker.visualisations.m_u_parameters_chart(),
            },
            {
                "chart_name": "unlinkables_chart",
                "chart": model.linker.evaluation.unlinkables_chart(),
            },
            {
                "chart_name": "validation_results_chart",
                "chart": model.validation_chart,
            },
            {
                "chart_name": "test_predictions_waterfall_chart",
                "chart": test_waterfall_chart,
            },
        ]
        for chart in charts_config:
            chart["chart"].save((log_dir / f"{chart['chart_name']}.html").absolute())

        json.dump(
            test_waterfall_chart_data,
            (log_dir / "test_predictions_waterfall_chart_data.json").open("w+"),
        )

    output_file = log_dir / f"training_results_{args.mode}_{timestamp}.json"
    logger.info("Writing logs file at path %s", output_file)
    with output_file.open("w") as f:
        json.dump(results, f)

    if df_pred_test is not None:
        output_df_preds_test_pred = (
            log_dir / f"training_{args.mode}_{timestamp}_test_pred_predictions.parquet"
        )
        logger.info(
            "Writing df predictions test pred parquet file at path %s",
            output_df_preds_test_pred,
        )
        df_pred_test.write_parquet(output_df_preds_test_pred)

    if df_clusters_test is not None:
        output_df_clusters_test_pred = (
            log_dir / f"training_{args.mode}_{timestamp}_test_pred_clusters.parquet"
        )
        logger.info(
            "Writing df clusters test pred parquet file at path %s",
            output_df_clusters_test_pred,
        )
        df_clusters_test.write_parquet(output_df_clusters_test_pred)

    logger.info("Results saved to %s", output_file)
