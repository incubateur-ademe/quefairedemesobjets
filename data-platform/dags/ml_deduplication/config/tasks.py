"""Task IDs for the ML-deduplication DAG"""

from dataclasses import dataclass


@dataclass(frozen=True)
class TASKS:
    CONFIG_CREATE = "ml_deduplication_config_create"
    SELECTION = "ml_deduplication_acteurs_select"
    CREATE_INSTANCE = "create_instance"
    WAIT_FOR_READY = "wait_for_ready"
    RUN_INFERENCE = "run_inference"
    CLUSTERS_SELECT = "ml_deduplication_clusters_select"
    PARENTS_CHOOSE_NEW = "ml_deduplication_parents_choose_new"
    PARENTS_CHOOSE_DATA = "ml_deduplication_parents_choose_data"
    SUGGESTIONS_PREPARE = "ml_deduplication_suggestions_prepare"
    SUGGESTIONS_TO_DB = "ml_deduplication_suggestions_to_db"
    SUGGESTIONS_FAILING = "ml_deduplication_suggestions_failing"
    CLEANUP = "ml_deduplication_cleanup"
    DESTROY_INSTANCE = "destroy_instance"
