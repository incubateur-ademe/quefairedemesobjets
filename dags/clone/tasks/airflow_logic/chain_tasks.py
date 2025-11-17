from airflow import DAG
from airflow.models.baseoperator import chain
from clone.tasks.airflow_logic.clone_config_create_task import clone_config_create_task
from clone.tasks.airflow_logic.clone_old_tables_remove_task import (
    clone_old_tables_remove_task,
)
from clone.tasks.airflow_logic.clone_table_create_task import clone_table_create_task
from clone.tasks.airflow_logic.clone_table_validate_task import (
    clone_table_validate_task,
)
from clone.tasks.airflow_logic.clone_view_in_use_switch_task import (
    clone_view_in_use_switch_task,
)
from shared.config.dag_names import REFRESH_GEO_MODELS_DAG_ID
from shared.tasks.airflow_logic.trigger_dag_task import trigger_dag_task


def chain_tasks(dag: DAG) -> None:
    chain(
        clone_config_create_task(dag),
        clone_table_create_task(dag),
        clone_table_validate_task(dag),
        clone_view_in_use_switch_task(dag),
        clone_old_tables_remove_task(dag),
        trigger_dag_task(
            task_id="launch_refresh_geo_models",
            target_dag=REFRESH_GEO_MODELS_DAG_ID,
        ),
    )
