import dedupe
import numpy as np

from sklearn.model_selection import ParameterGrid

from ml_deduplication.training.utils import partition_to_dict
from ml_deduplication.evaluation.metrics import fbeta
from ml_deduplication.evaluation.metrics.pairwise import pairwise_metrics_from_clusters
from ml_deduplication.training.features import (
    DEDUPE_VARIABLES_CONFIG_MANDATORY,
    DEDUPE_VARIABLES_CONFIG_RESTRICTED,
    DEDUPE_VARIABLES_CONFIG_FULL,
    FEATURES_NAMES_FROM_DATASET,
)


def select_best_threshold(
    deduper: dedupe.Dedupe,
    entities_dev: dict,
    id_to_cluster_id_dev: dict,
    thresholds=np.arange(0.10, 1.00, 0.05),
    min_recall: float = 0.3,
) -> tuple[float, dict]:
    """
    Teste une grille de seuils sur le jeu de dev et choisit celui qui :
      - maximise la précision, parmi les seuils qui respectent un rappel
        minimal (`min_recall`) ;
      - à défaut (aucun seuil ne respecte le rappel minimal), maximise le
        F-bêta (bêta=0.5, qui pondère davantage la précision).

    La précision/rappel est calculée de façon EXHAUSTIVE sur toutes les
    entités du dev ayant une vérité terrain connue (via `clusters_df`),
    et non sur le seul sous-échantillon de paires annotées : cela évite
    d'ignorer les faux positifs "inventés" par le clustering de dedupe.

    NB : on relance `partition()` pour chaque seuil (simplification). Sur
    un très gros volume, on pourrait factoriser le blocking/scoring et ne
    faire varier que l'étape de clustering.
    """
    eval_ids = set(id_to_cluster_id_dev.keys())

    results = []
    for t in thresholds:
        # On demande à dedupe de clusteriser et on obtient une
        # liste de liste d'ids regroupés
        partition_pred = deduper.partition(entities_dev, float(t))

        # On crée un dict entity_id -> cluster_id + singleton
        id_to_cluster_pred = partition_to_dict(partition_pred)
        # On s'assure qu'il n'y ait que des ids du jeu d'évaluation
        id_to_cluster_pred = {i: id_to_cluster_pred[i] for i in eval_ids}

        # On calcule les métriques en comparant
        metrics = pairwise_metrics_from_clusters(
            id_to_cluster_id_dev, id_to_cluster_pred
        )
        results.append((float(t), metrics))
        print(
            f"  seuil={t:.2f}  precision={metrics['precision']:.3f}  "
            f"recall={metrics['recall']:.3f}  f1={metrics['f1']:.3f}"
        )
        print("-----")

    # 1) parmi les seuils respectant le rappel minimal, on prend le plus précis
    eligibles = [(t, m) for t, m in results if m["recall"] >= min_recall]
    if eligibles:
        return max(eligibles, key=lambda x: x[1]["precision"])

    # 2) sinon, repli sur le F-bêta (favorise quand même la précision)
    return max(
        results, key=lambda x: fbeta(x[1]["precision"], x[1]["recall"], beta=0.5)
    )


def generate_parameter_grid() -> ParameterGrid:
    param_grid = {
        "index_predicates": [True, False],
        "dedupe_variables_config": [
            DEDUPE_VARIABLES_CONFIG_MANDATORY,
            DEDUPE_VARIABLES_CONFIG_RESTRICTED,
            DEDUPE_VARIABLES_CONFIG_FULL,
        ],
        "features_names": [FEATURES_NAMES_FROM_DATASET],
    }

    return ParameterGrid(param_grid)
