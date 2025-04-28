from airflow import DAG
from airflow.models.baseoperator import chain
from clone.tasks.airflow_logic.clone_config_create_task import (
    clone_config_create_task,
)
from clone.tasks.airflow_logic.clone_old_tables_remove_task import (
    clone_old_tables_remove_task,
)
from clone.tasks.airflow_logic.clone_table_create_task import (
    clone_table_create_task,
)
from clone.tasks.airflow_logic.clone_table_validate_task import (
    clone_table_validate_task,
)
from clone.tasks.airflow_logic.clone_view_in_use_switch_task import (
    clone_view_in_use_switch_task,
)


def chain_tasks(dag: DAG) -> None:
    chain(
        clone_config_create_task(dag),
        clone_table_create_task(dag),
        clone_table_validate_task(dag),
        clone_view_in_use_switch_task(dag),
        clone_old_tables_remove_task(dag),
    )
