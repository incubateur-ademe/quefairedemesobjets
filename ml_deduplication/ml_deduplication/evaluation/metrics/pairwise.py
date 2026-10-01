from collections import Counter
from math import comb

import numpy as np
from sklearn.metrics import average_precision_score, roc_auc_score

from ml_deduplication.evaluation.metrics import fbeta


def pairwise_metrics_from_clusters(true_clusters: dict, pred_clusters: dict) -> dict:
    """
    Precision / recall / F1 au niveau paire, calculés de façon EXHAUSTIVE
    sur toutes les paires possibles entre les entités considérées (et pas
    seulement sur les paires présentes dans `pairs_df`).

    En effet, `deduper.partition()` regroupe les entités en clusters : deux
    entités peuvent se retrouver dans le même cluster prédit sans avoir
    jamais formé une paire annotée dans le dataframe de base. Ignorer ces
    paires "nouvelles" revient à ne jamais compter certains faux positifs
    (ni certains faux négatifs pour des paires vraies non couvertes par
    l'échantillon), ce qui biaise la métrique à la hausse.

    On évite d'énumérer explicitement les O(n²) paires en s'appuyant sur
    une formule combinatoire à partir des tailles de clusters (vrais,
    prédits, et intersections vrai×prédit) : pour un groupe de taille n,
    il y a C(n,2) paires internes.

    `true_clusters` et `pred_clusters` doivent couvrir exactement le même
    ensemble d'identifiants (typiquement : toutes les entités du split
    évalué pour lesquelles la vérité terrain est connue).
    """
    ids = list(true_clusters.keys())
    assert set(ids) == set(
        pred_clusters.keys()
    ), "true_clusters et pred_clusters doivent couvrir les mêmes ids"

    # nb de paires prédites comme duplicats = somme des C(taille,2) par cluster prédit
    pred_sizes = Counter(pred_clusters[i] for i in ids)
    predicted_positive = sum(comb(n, 2) for n in pred_sizes.values())

    # nb de paires réellement duplicats = somme des C(taille,2) par cluster vrai
    true_sizes = Counter(true_clusters[i] for i in ids)
    actual_positive = sum(comb(n, 2) for n in true_sizes.values())

    # vrais positifs = paires qui sont ensemble à la fois dans le cluster prédit
    # ET le cluster vrai
    joint_sizes = Counter((pred_clusters[i], true_clusters[i]) for i in ids)
    tp = sum(comb(n, 2) for n in joint_sizes.values())

    fp = predicted_positive - tp
    fn = actual_positive - tp

    precision = tp / (tp + fp) if (tp + fp) else 0.0
    recall = tp / (tp + fn) if (tp + fn) else 0.0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) else 0.0
    fbeta_score = fbeta(precision, recall, beta=0.5)
    return {
        "precision": precision,
        "recall": recall,
        "f1": f1,
        "fbeta": fbeta_score,
        "tp": tp,
        "fp": fp,
        "fn": fn,
    }


def pairwise_metrics_from_scores(scores: np.ndarray, y: np.ndarray) -> dict:

    roc_auc = roc_auc_score(y, scores)
    pr_auc = average_precision_score(y, scores)
    pos_mean_score = scores[y == 1].mean().item()
    neg_mean_score = scores[y == 0].mean().item()

    return {
        "roc_auc": roc_auc,
        "pr_auc": pr_auc,
        "pos_mean_score": pos_mean_score,
        "neg_mean_score": neg_mean_score,
    }
