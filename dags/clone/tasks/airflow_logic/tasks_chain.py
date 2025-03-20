from airflow import DAG
from airflow.models.baseoperator import chain
from clone.tasks.airflow_logic.clone_ae_old_tables_remove_task import (
    clone_ea_old_tables_remove_task,
)
from clone.tasks.airflow_logic.clone_ae_table_create_task import (
    clone_ea_table_create_task,
)
from clone.tasks.airflow_logic.clone_ae_table_name_prepare_task import (
    clone_ea_table_name_prepare_task,
)
from clone.tasks.airflow_logic.clone_ae_table_validate_task import (
    clone_ea_table_validate_unite_task,
)
from clone.tasks.airflow_logic.clone_ae_view_in_use_switch_task import (
    clone_ea_view_in_use_switch_task,
)


def tasks_chain(dag: DAG) -> None:

    chain(
        clone_ea_table_name_prepare_task(dag),
        clone_ea_table_create_task(dag),
        clone_ea_table_validate_unite_task(dag),
        clone_ea_view_in_use_switch_task(dag),
        clone_ea_old_tables_remove_task(dag),
    )
