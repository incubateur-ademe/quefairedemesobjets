from collections import Counter
from math import comb


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
    return {
        "precision": precision,
        "recall": recall,
        "f1": f1,
        "tp": tp,
        "fp": fp,
        "fn": fn,
    }
