"""Assemble the ML-deduplication DAG task graph."""

from airflow.sdk.bases.operator import chain
from ml_deduplication.tasks.airflow_logic.acteurs_select_task import (
    ml_deduplication_acteurs_select_task,
)
from ml_deduplication.tasks.airflow_logic.cleanup_task import (
    ml_deduplication_cleanup_task,
)
from ml_deduplication.tasks.airflow_logic.clusters_select_task import (
    ml_deduplication_clusters_select_task,
)
from ml_deduplication.tasks.airflow_logic.config_create_task import (
    ml_deduplication_config_create_task,
)
from ml_deduplication.tasks.airflow_logic.parents_choose_data_task import (
    ml_deduplication_parents_choose_data_task,
)
from ml_deduplication.tasks.airflow_logic.parents_choose_new_task import (
    ml_deduplication_parents_choose_new_task,
)
from ml_deduplication.tasks.airflow_logic.suggestions_failing_task import (
    ml_deduplication_suggestions_failing_task,
)
from ml_deduplication.tasks.airflow_logic.suggestions_prepare_task import (
    ml_deduplication_suggestions_prepare_task,
)
from ml_deduplication.tasks.airflow_logic.suggestions_to_db_task import (
    ml_deduplication_suggestions_to_db_task,
)


def chain_tasks(fields_all: list[str], instance_ops: dict) -> None:
    """Build the full task graph.

    Operators auto-bind to the ambient `dag` context when created inside the
    `@dag`-decorated function, so no explicit dag reference is needed here.

    Args:
        fields_all: all selectable acteur data columns.
        instance_ops: dict with the BashOperators built in the DAG file
            (create_instance, wait_for_ready, run_inference, destroy_instance).
    """
    config_create = ml_deduplication_config_create_task(fields_all)
    acteurs_select = ml_deduplication_acteurs_select_task()
    clusters_select = ml_deduplication_clusters_select_task()
    parents_choose_new = ml_deduplication_parents_choose_new_task()
    parents_choose_data = ml_deduplication_parents_choose_data_task()
    suggestions_prepare = ml_deduplication_suggestions_prepare_task()
    suggestions_to_db = ml_deduplication_suggestions_to_db_task()
    suggestions_failing = ml_deduplication_suggestions_failing_task()
    cleanup = ml_deduplication_cleanup_task()

    chain(
        config_create,
        acteurs_select,
        instance_ops["create_instance"],
        instance_ops["wait_for_ready"],
        instance_ops["run_inference"],
        clusters_select,
        parents_choose_new,
        parents_choose_data,
        suggestions_prepare,
        suggestions_to_db,
        suggestions_failing,
    )

    # Always clean up, whether or not upstream tasks succeeded.
    instance_ops["run_inference"] >> instance_ops["destroy_instance"]
    suggestions_failing >> cleanup
