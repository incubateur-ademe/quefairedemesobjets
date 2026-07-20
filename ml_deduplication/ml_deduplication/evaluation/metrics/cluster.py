"""
Métriques d'évaluation du clustering pour la résolution d'entités (déduplication).

Ces fonctions complètent `pairwise_metrics_from_clusters` (précision/rappel/F1
au niveau PAIRE) par des métriques au niveau CLUSTER, qui permettent de mieux
diagnostiquer le TYPE d'erreurs commises par le modèle, pas seulement leur
volume :
    - un cluster prédit qui mélange deux vrais clusters (sur-fusion, perte
      de précision)
    - un vrai cluster éclaté en plusieurs clusters prédits (sous-fusion,
      perte de rappel)

Toutes les fonctions prennent en entrée deux dicts `{id: cluster_id}`
(même format que `pairwise_metrics_from_clusters`) et doivent couvrir
exactement le même ensemble d'ids.
"""

import logging
from collections import defaultdict
from typing import Hashable

logger = logging.getLogger(__name__)


def invert_cluster_dict(id_to_cluster: dict[Hashable, Hashable]) -> dict[Hashable, set]:
    """Regroupe les ids par cluster à partir d'un dict id -> cluster_id."""
    clusters: dict[Hashable, set] = defaultdict(set)
    for id_, cluster_id in id_to_cluster.items():
        clusters[cluster_id].add(id_)
    return dict(clusters)


def _check_same_ids(true_clusters: dict, pred_clusters: dict) -> None:
    assert set(true_clusters.keys()) == set(
        pred_clusters.keys()
    ), "true_clusters et pred_clusters doivent couvrir les mêmes ids"


def exact_match_cluster_metrics(true_clusters: dict, pred_clusters: dict) -> dict:
    """
    Précision / rappel / F1 au niveau cluster, version stricte "exact match" :
    un cluster prédit compte comme vrai positif seulement s'il est
    RIGOUREUSEMENT identique (même ensemble d'ids) à un cluster vérité
    terrain. Un seul id en trop ou en moins fait échouer tout le cluster.

    -> Répond littéralement à "combien de mes clusters prédits sont
    parfaits ?". C'est la métrique la plus sévère de ce module : à
    utiliser comme repère "best case", pas comme métrique principale de
    pilotage (elle traite un cluster de 2 et un cluster de 50 à égalité).
    """
    _check_same_ids(true_clusters, pred_clusters)

    true_sets = {frozenset(ids) for ids in invert_cluster_dict(true_clusters).values()}
    pred_sets = {frozenset(ids) for ids in invert_cluster_dict(pred_clusters).values()}

    exact_matches = true_sets & pred_sets

    precision = len(exact_matches) / len(pred_sets) if pred_sets else 0.0
    recall = len(exact_matches) / len(true_sets) if true_sets else 0.0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) else 0.0

    return {
        "precision": precision,
        "recall": recall,
        "f1": f1,
        "n_exact_matches": len(exact_matches),
        "n_pred_clusters": len(pred_sets),
        "n_true_clusters": len(true_sets),
    }


def bcubed_metrics(true_clusters: dict, pred_clusters: dict) -> dict:
    """
    Précision / rappel B-cubed (Bagga & Baldwin, 1998) : calculés PAR ENTITÉ
    puis moyennés, ce qui pondère naturellement par la taille des clusters.

    Pour chaque entité e :
        precision(e) = |cluster_pred(e) ∩ cluster_vrai(e)| / |cluster_pred(e)|
        recall(e)    = |cluster_pred(e) ∩ cluster_vrai(e)| / |cluster_vrai(e)|
    puis on moyenne sur toutes les entités.

    -> C'est la métrique de référence en résolution d'entités dans la
    littérature académique, un bon compromis entre le pairwise (généreux
    sur les gros clusters) et l'exact match (trop sévère). C'est souvent
    la métrique à privilégier si vous devez n'en garder qu'une en plus du
    pairwise F1 que vous avez déjà.
    """
    _check_same_ids(true_clusters, pred_clusters)

    true_groups = invert_cluster_dict(true_clusters)
    pred_groups = invert_cluster_dict(pred_clusters)

    precisions = []
    recalls = []
    for id_ in true_clusters:
        true_group = true_groups[true_clusters[id_]]
        pred_group = pred_groups[pred_clusters[id_]]
        intersection = len(true_group & pred_group)
        precisions.append(intersection / len(pred_group))
        recalls.append(intersection / len(true_group))

    precision = sum(precisions) / len(precisions)
    recall = sum(recalls) / len(recalls)
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) else 0.0

    return {"precision": precision, "recall": recall, "f1": f1}


def cluster_purity_report(
    true_clusters: dict, pred_clusters: dict, exclude_singletons: bool = False
) -> dict:
    """
    Classe chaque cluster PRÉDIT en 3 catégories, en regardant à quel(s)
    cluster(s) vérité terrain appartiennent ses membres :

      - "exact"        : pur ET complet -> correspond exactement à un vrai
                          cluster
      - "under_merged"  : pur mais incomplet -> tous les membres viennent
                          du même vrai cluster, mais il en manque
                          (rappel perdu : des doublons n'ont pas été trouvés)
      - "over_merged"   : impur -> mélange des entités venant de vrais
                          clusters différents (précision perdue : le
                          modèle a fusionné des entités distinctes)

    C'est la métrique la plus directement actionnable : `over_merged`
    pointe vers des faux positifs à corriger (règles métier, seuil trop
    bas), `under_merged` vers du rappel à gagner (seuil trop haut,
    blocking insuffisant).

    exclude_singletons: si True, ignore les clusters prédits d'une seule
        entité dans les pourcentages (sinon ils comptent trivialement
        comme "exact" ou "under_merged", ce qui peut gonfler le score si
        votre dataset contient beaucoup de vrais singletons).
    """
    _check_same_ids(true_clusters, pred_clusters)

    pred_groups = invert_cluster_dict(pred_clusters)
    true_groups = invert_cluster_dict(true_clusters)

    exact, under_merged, over_merged = [], [], []

    for pred_cluster_id, member_ids in pred_groups.items():
        if exclude_singletons and len(member_ids) == 1:
            continue
        true_labels = {true_clusters[i] for i in member_ids}
        if len(true_labels) == 1:
            true_cluster_id = next(iter(true_labels))
            if member_ids == true_groups[true_cluster_id]:
                exact.append(pred_cluster_id)
            else:
                under_merged.append(pred_cluster_id)
        else:
            over_merged.append(pred_cluster_id)

    n_pred = len(exact) + len(under_merged) + len(over_merged)
    return {
        "n_pred_clusters": n_pred,
        "n_exact": len(exact),
        "n_under_merged": len(under_merged),
        "n_over_merged": len(over_merged),
        "pct_exact": len(exact) / n_pred if n_pred else 0.0,
        "pct_pure": (len(exact) + len(under_merged)) / n_pred if n_pred else 0.0,
        "pct_over_merged": len(over_merged) / n_pred if n_pred else 0.0,
        "over_merged_cluster_ids": over_merged,
        "under_merged_cluster_ids": under_merged,
    }


def cluster_split_report(
    true_clusters: dict, pred_clusters: dict, top_n: int = 10
) -> dict:
    """
    Symétrique de `cluster_purity_report`, mais vu côté vérité terrain :
    pour chaque vrai cluster, sur combien de clusters prédits DIFFÉRENTS
    ses membres ont-ils été éclatés ? Idéalement 1 (pas de split).

    Utile pour repérer les gros vrais clusters que le modèle a du mal à
    reconstituer entièrement (souvent des chaînes/franchises avec
    beaucoup de variantes de nom/adresse).
    """
    _check_same_ids(true_clusters, pred_clusters)

    true_groups = invert_cluster_dict(true_clusters)
    split_counts = {
        true_id: len({pred_clusters[i] for i in members})
        for true_id, members in true_groups.items()
    }
    n_true = len(true_groups)
    n_not_split = sum(1 for c in split_counts.values() if c == 1)

    return {
        "n_true_clusters": n_true,
        "n_not_split": n_not_split,
        "pct_not_split": n_not_split / n_true if n_true else 0.0,
        "avg_split_factor": sum(split_counts.values()) / n_true if n_true else 0.0,
        "most_split_clusters": sorted(split_counts.items(), key=lambda kv: -kv[1])[
            :top_n
        ],
    }


def sklearn_cluster_metrics(true_clusters: dict, pred_clusters: dict) -> dict:
    """
    Métriques de clustering génériques (indépendantes du domaine), utiles
    en sanity-check rapide : ARI (Adjusted Rand Index) et homogénéité /
    complétude / V-measure.

    homogeneity ~ équivalent info-théorique de la "pureté" (pct_pure
    ci-dessus), completeness ~ équivalent de "pas splitté"
    (pct_not_split ci-dessus), mais en continu plutôt qu'en comptage de
    clusters. Bon indicateur de synthèse à suivre d'un run à l'autre.
    """
    from sklearn.metrics import adjusted_rand_score, homogeneity_completeness_v_measure

    ids = sorted(true_clusters.keys())
    y_true = [true_clusters[i] for i in ids]
    y_pred = [pred_clusters[i] for i in ids]

    ari = adjusted_rand_score(y_true, y_pred)
    homogeneity, completeness, v_measure = homogeneity_completeness_v_measure(
        y_true, y_pred
    )
    return {
        "ari": ari,
        "homogeneity": homogeneity,
        "completeness": completeness,
        "v_measure": v_measure,
    }


def generate_full_cluster_report(
    id_to_cluster_id_true_dict: dict, id_to_cluster_id_pred_dict: dict
) -> dict:
    """Calcule toutes les métriques ci-dessus en un seul appel."""
    return {
        "exact_match": exact_match_cluster_metrics(
            id_to_cluster_id_true_dict, id_to_cluster_id_pred_dict
        ),
        "bcubed": bcubed_metrics(
            id_to_cluster_id_true_dict, id_to_cluster_id_pred_dict
        ),
        "purity": cluster_purity_report(
            id_to_cluster_id_true_dict, id_to_cluster_id_pred_dict
        ),
        "split": cluster_split_report(
            id_to_cluster_id_true_dict, id_to_cluster_id_pred_dict
        ),
        "sklearn": sklearn_cluster_metrics(
            id_to_cluster_id_true_dict, id_to_cluster_id_pred_dict
        ),
    }


def print_debug_cluster_report(true_clusters: dict, pred_clusters: dict) -> None:
    """Affiche un résumé lisible, dans le même esprit que vos logger.debugs de
    `select_best_threshold`."""
    report = generate_full_cluster_report(true_clusters, pred_clusters)

    em = report["exact_match"]
    bc = report["bcubed"]
    pu = report["purity"]
    sp = report["split"]
    sk = report["sklearn"]

    logger.debug(
        f"Exact match  : precision={em['precision']:.3f}  recall={em['recall']:.3f}  "
        f"f1={em['f1']:.3f}  ({em['n_exact_matches']}/{em['n_pred_clusters']} clusters prédits exacts)"
    )
    logger.debug(
        f"B-cubed      : precision={bc['precision']:.3f}  recall={bc['recall']:.3f}  f1={bc['f1']:.3f}"
    )
    logger.debug(
        f"Pureté       : {pu['pct_exact']:.1%} exacts, {pu['pct_pure']:.1%} purs, "
        f"{pu['pct_over_merged']:.1%} sur-fusionnés ({pu['n_over_merged']} clusters à inspecter)"
    )
    logger.debug(
        f"Splits       : {sp['pct_not_split']:.1%} des vrais clusters non éclatés "
        f"(facteur de split moyen={sp['avg_split_factor']:.2f})"
    )
    logger.debug(
        f"Sklearn      : ARI={sk['ari']:.3f}  homogeneity={sk['homogeneity']:.3f}  "
        f"completeness={sk['completeness']:.3f}  v_measure={sk['v_measure']:.3f}"
    )


if __name__ == "__main__":
    # exemple de sanity check : 2 vrais clusters (3 + 2 entités),
    # le modèle sur-fusionne le premier (mélange avec 1 entité du 2e) et
    # sous-fusionne/splitte le second.
    true_clusters = {"a": "c1", "b": "c1", "c": "c1", "d": "c2", "e": "c2"}
    pred_clusters = {"a": "p1", "b": "p1", "c": "p1", "d": "p1", "e": "p2"}

    print_debug_cluster_report(true_clusters, pred_clusters)
