from airflow import DAG
from airflow.sdk.bases.operator import chain
from clone.tasks.airflow_logic.clone_config_create_task import clone_config_create_task
from clone.tasks.airflow_logic.clone_dbt_task import (
    PARAM_DBT_RUN_COMMAND,
    clone_dbt_run_task,
    clone_dbt_test_task,
)
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


def chain_tasks(dag: DAG) -> None:
    """Build the shared clone chain.

    When the DAG exposes the DBT command params (added via ``clone_dbt_params``),
    a DBT normalization run followed by its tests is inserted after the in-use
    view switch. DAGs without those params keep their chain unchanged.
    """
    tasks = [
        clone_config_create_task(dag),
        clone_table_create_task(dag),
        clone_table_validate_task(dag),
        clone_view_in_use_switch_task(dag),
        clone_old_tables_remove_task(dag),
    ]

    if PARAM_DBT_RUN_COMMAND in dag.params:
        tasks += [
            clone_dbt_run_task(dag),
            clone_dbt_test_task(dag),
        ]

    chain(*tasks)
