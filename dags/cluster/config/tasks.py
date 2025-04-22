"""Task IDs for the clustering DAG"""

from dataclasses import dataclass


@dataclass(frozen=True)
class TASKS:
    CONFIG_CREATE = "cluster_acteurs_config_create"
    SELECTION = "cluster_acteurs_read"
    NORMALIZE = "cluster_acteurs_normalize"
    PARENTS_CHOOSE_NEW = "cluster_acteurs_parents_choose_new"
    PARENTS_CHOOSE_DATA = "cluster_acteurs_parents_choose_data"
    CLUSTERS_PREPARE = "cluster_acteurs_clusters_prepare"
    CLUSTERS_VALIDATE = "cluster_acteurs_clusters_validate"
    SUGGESTIONS_PREPARE = "cluster_acteurs_suggestions_prepare"
    SUGGESTIONS_TO_DB = "cluster_acteurs_suggestions_to_db"
    SUGGESTIONS_FAILING = "cluster_acteurs_suggestions_failing"
