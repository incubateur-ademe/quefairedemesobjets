from collections.abc import Iterable

import polars as pl
from ml_deduplication.evaluation.metrics.cluster import generate_full_cluster_report
from ml_deduplication.evaluation.metrics.pairwise import (
    pairwise_metrics_from_clusters,
)
from ml_deduplication.training.utils import (
    create_acteur_to_cluster_dict,
)
from sklearn.metrics import (
    confusion_matrix,
    fbeta_score,
    precision_score,
    recall_score,
)


def compute_pairwise_metrics_at_thresholds(
    df_predicitons_oof: pl.DataFrame, candidate_threshold: Iterable
) -> pl.DataFrame:
    results = []
    y_true = df_predicitons_oof["label"]
    for threshold in candidate_threshold:
        y_pred = df_predicitons_oof["score_true_calibrated"] >= threshold
        tn, fp, fn, tp = confusion_matrix(y_true, y_pred).ravel().tolist()
        results.append(
            {
                "threshold": threshold,
                "tp": tp,
                "fp": fp,
                "tn": tn,
                "fn": fn,
                "precision": precision_score(y_true, y_pred),
                "recall": recall_score(y_true, y_pred),
                "fbeta": fbeta_score(y_true, y_pred, beta=0.33),
            }
        )

    return pl.DataFrame(results)


def generate_performance_reports(
    df_entities_true: pl.DataFrame, df_cluster_pred: pl.DataFrame
) -> dict:
    cluster_to_acteur_dict_test = {
        e["cluster_id_split"]: e["identifiant_unique"]
        for e in df_entities_true.group_by("cluster_id_split")
        .agg("identifiant_unique")
        .to_dicts()
    }
    acteur_to_cluster_id_dict_test = create_acteur_to_cluster_dict(
        cluster_to_acteur_dict_test
    )

    cluster_to_acteur_dict_pred_test = {
        e["cluster_id"]: e["entity_id"]
        for e in df_cluster_pred.group_by("cluster_id").agg("entity_id").to_dicts()
    }
    acteur_to_cluster_id_dict_pred_test = create_acteur_to_cluster_dict(
        cluster_to_acteur_dict_pred_test
    )

    test_score_metrics = pairwise_metrics_from_clusters(
        acteur_to_cluster_id_dict_test, acteur_to_cluster_id_dict_pred_test
    )

    clusterwise_metrics = generate_full_cluster_report(
        acteur_to_cluster_id_dict_test, acteur_to_cluster_id_dict_pred_test
    )

    return {
        "pairwise": {**test_score_metrics},
        "clusterwise": clusterwise_metrics,
    }
