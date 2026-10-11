"""Tests for the pairwise evaluation metrics.

`pairwise_metrics_from_clusters` computes precision / recall / F1 at the pair
level, exhaustively over all possible pairs implied by the clusters, using a
combinatorial formula (C(n,2) internal pairs per cluster).
"""

import numpy as np
import pytest

from ml_deduplication.evaluation.metrics.pairwise import (
    pairwise_metrics_from_clusters,
    pairwise_metrics_from_scores,
)


class TestPairwiseMetricsFromClusters:
    def test_perfect_prediction(self):
        # true and predicted identical: every entity grouped the same way
        true = {"a": 1, "b": 1, "c": 2, "d": 2}
        pred = {"a": "x", "b": "x", "c": "y", "d": "y"}
        m = pairwise_metrics_from_clusters(true, pred)
        assert m["precision"] == pytest.approx(1.0)
        assert m["recall"] == pytest.approx(1.0)
        assert m["f1"] == pytest.approx(1.0)
        assert m["tp"] == 2
        assert m["fp"] == 0
        assert m["fn"] == 0

    def test_single_cluster_split(self):
        # true: a & b are duplicates; pred: all singletons -> recall 0
        true = {"a": 1, "b": 1}
        pred = {"a": "x", "b": "y"}
        m = pairwise_metrics_from_clusters(true, pred)
        assert m["recall"] == pytest.approx(0.0)
        assert m["precision"] == pytest.approx(0.0)
        assert m["f1"] == pytest.approx(0.0)
        assert m["tp"] == 0
        assert m["fn"] == 1

    def test_false_positive_merges(self):
        # true: {a,b}, {c}, {d}; pred: {a,b}, {c,d}
        # tp = 1 pair (a,b); fp = 1 pair (c,d); no fn
        true = {"a": 1, "b": 1, "c": 2, "d": 3}
        pred = {"a": "x", "b": "x", "c": "y", "d": "y"}
        m = pairwise_metrics_from_clusters(true, pred)
        assert m["tp"] == 1
        assert m["fp"] == 1
        assert m["fn"] == 0
        assert m["precision"] == pytest.approx(0.5)
        assert m["recall"] == pytest.approx(1.0)
        assert m["f1"] == pytest.approx(2 * 0.5 * 1.0 / (0.5 + 1.0))
        assert m["fbeta"] == pytest.approx(1.25 * 0.5 * 1.0 / (0.25 * 0.5 + 1.0))

    def test_missing_positive_pair(self):
        # true: {a,b}; pred: {a,b,c} -> tp=(a,b), fp=(a,c),(b,c), fn=0
        true = {"a": 1, "b": 1, "c": 2}
        pred = {"a": "x", "b": "x", "c": "x"}
        m = pairwise_metrics_from_clusters(true, pred)
        assert m["tp"] == 1
        assert m["fp"] == 2
        assert m["fn"] == 0
        assert m["precision"] == pytest.approx(1 / 3)

    def test_requires_same_entity_sets(self):
        true = {"a": 1, "b": 1}
        pred = {"a": "x"}  # b missing
        with pytest.raises(AssertionError):
            pairwise_metrics_from_clusters(true, pred)

    def test_larger_cluster_pair_count(self):
        # predicted: one cluster of 3 -> C(3,2)=3 predicted positive pairs
        true = {"a": 1, "b": 1, "c": 2}
        pred = {"a": "x", "b": "x", "c": "x"}
        assert pairwise_metrics_from_clusters(true, pred)["fp"] == 2


class TestPairwiseMetricsFromScores:
    def test_separated_scores(self):
        y = np.array([0, 1])
        scores = np.array([0.1, 0.9])
        m = pairwise_metrics_from_scores(scores, y)
        assert m["roc_auc"] == pytest.approx(1.0)
        assert m["pr_auc"] == pytest.approx(1.0)
        assert m["pos_mean_score"] == pytest.approx(0.9)
        assert m["neg_mean_score"] == pytest.approx(0.1)
