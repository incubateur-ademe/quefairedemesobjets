from datetime import datetime
import io
import json
import logging
from pathlib import Path

import dedupe
import polars as pl

from ml_deduplication.evaluation.metrics.pairwise import pairwise_metrics_from_clusters
from ml_deduplication.training.features import (
    DEDUPE_VARIABLE_CONFIG,
    FEATURES_NAMES_FROM_DATASET,
)
from ml_deduplication.training.model import BusinessRulesDedupe
from ml_deduplication.training.model_selection import select_best_threshold
from ml_deduplication.training.utils import (
    build_entities_dict,
    create_acteur_to_cluster_dict,
    create_cluster_to_acteurs_dict,
    partition_to_dict,
    partition_to_results_dict,
    split_train_dev,
)

logging.basicConfig(
    level=logging.DEBUG, format="%(asctime)s | %(filename)s | %(message)s"
)
logger = logging.getLogger(__name__)


LOGS_FOLDER = Path(__file__).parent.parent.parent / "logs"


def train_deduper(
    df_train: pl.DataFrame, entities_dict: dict, dedupe_variables_definition: list
) -> BusinessRulesDedupe:
    """
    Entraîne un objet dedupe.Dedupe à partir des paires labellisées de
    `df_train_sub`, sans passer par l'apprentissage actif interactif.

    entities contient tous les acteurs dans un dictionnaire format dedupe.
    """

    deduper = BusinessRulesDedupe(dedupe_variables_definition)

    train_ids = set(df_train["identifiant_unique_i"].to_list()) | set(
        df_train["identifiant_unique_j"].to_list()
    )
    train_entities = {i: entities_dict[i] for i in train_ids}

    # Construct labeled_pairs before training
    labeled_pairs = {"match": [], "distinct": []}
    for row in df_train.iter_rows(named=True):
        pair = (
            entities_dict[row["identifiant_unique_i"]],
            entities_dict[row["identifiant_unique_j"]],
        )
        labeled_pairs["match" if row["label"] else "distinct"].append(pair)

    # Serialize labeled_pairs to a training file in memory
    training_file = io.StringIO()
    dedupe.write_training(labeled_pairs, training_file)
    training_file.seek(0)

    # use the serialized training file to avoid using mark_pairs
    # that can cause bugs depending of sample size
    deduper.prepare_training(
        train_entities,
        training_file=training_file,
        sample_size=max(10000, len(train_ids)),
    )

    deduper.train()
    deduper.cleanup_training()

    return deduper


# def run_training_with_hyperparameter_tuning():


def run_pipeline(df_features: pl.DataFrame):

    results = {}

    # Create cluster to ids dict
    cluster_to_acteur_dict = create_cluster_to_acteurs_dict(df_features)

    # Create id to cluster dict
    acteur_to_cluster_id_dict = create_acteur_to_cluster_dict(cluster_to_acteur_dict)

    # select features
    features_names = FEATURES_NAMES_FROM_DATASET
    # Create entities dict
    entities_dict = build_entities_dict(df_features, feature_names=features_names)

    # split train into train/dev
    df_train, df_dev = split_train_dev(df_features.filter(pl.col("split") == "train"))

    # config variables
    dedupe_variable_config = DEDUPE_VARIABLE_CONFIG

    # train dedupe
    logger.info("Starting dedupe training")
    deduper = train_deduper(df_train, entities_dict, dedupe_variable_config)
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
    deduper = train_deduper(
        df_features.filter(pl.col("split") == "train"),
        entities_dict,
        dedupe_variable_config,
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
    partition_test = deduper.partition(
        data=entities_dict_test, threshold=best_threshold
    )  # type: ignore
    id_to_cluster_test_pred = partition_to_dict(partition_test)
    metrics = pairwise_metrics_from_clusters(
        id_to_cluster_id_dict_test, id_to_cluster_test_pred
    )
    logger.info("Test metrics: %s", metrics)
    results["test_results"] = metrics
    results["pred_clusters"] = partition_to_results_dict(partition_test)

    with (LOGS_FOLDER / f"training_results_{datetime.now():%Y_%m_%d_%H%M}.json").open(
        "w"
    ) as f:
        json.dump(results, f)


if __name__ == "__main__":
    df_features = pl.read_parquet("datasets/features_dataset_20260718.parquet")
    run_pipeline(df_features)
