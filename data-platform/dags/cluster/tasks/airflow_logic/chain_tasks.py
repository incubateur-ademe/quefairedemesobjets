from airflow import DAG
from airflow.sdk.bases.operator import chain
from cluster.tasks.airflow_logic.cluster_acteurs_clusters_prepare_task import (
    cluster_acteurs_clusters_prepare_task,
)
from cluster.tasks.airflow_logic.cluster_acteurs_clusters_validate_task import (
    cluster_acteurs_clusters_validate_task,
)
from cluster.tasks.airflow_logic.cluster_acteurs_config_create_task import (
    cluster_acteurs_config_create_task,
)
from cluster.tasks.airflow_logic.cluster_acteurs_normalize_task import (
    cluster_acteurs_normalize_task,
)
from cluster.tasks.airflow_logic.cluster_acteurs_parents_choose_data_task import (
    cluster_acteurs_parents_choose_data_task,
)
from cluster.tasks.airflow_logic.cluster_acteurs_parents_choose_new_task import (
    cluster_acteurs_parents_choose_new_task,
)
from cluster.tasks.airflow_logic.cluster_acteurs_read_task import (
    cluster_acteurs_read_task,
)
from cluster.tasks.airflow_logic.cluster_acteurs_suggestions_failing_task import (
    cluster_acteurs_suggestions_failing_task,
)
from cluster.tasks.airflow_logic.cluster_acteurs_suggestions_prepare_task import (
    cluster_acteurs_suggestions_prepare_task,
)
from cluster.tasks.airflow_logic.cluster_acteurs_suggestions_to_db_task import (
    cluster_acteurs_suggestions_to_db_task,
)


def chain_tasks(dag: DAG) -> None:

    chain(
        cluster_acteurs_config_create_task(dag),
        cluster_acteurs_read_task(dag),
        cluster_acteurs_normalize_task(dag),
        cluster_acteurs_clusters_prepare_task(dag),
        cluster_acteurs_clusters_validate_task(dag),
        cluster_acteurs_parents_choose_new_task(dag),
        cluster_acteurs_parents_choose_data_task(dag),
        cluster_acteurs_suggestions_prepare_task(dag),
        cluster_acteurs_suggestions_to_db_task(dag),
        cluster_acteurs_suggestions_failing_task(dag),
    )
