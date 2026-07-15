from datetime import datetime

from airflow import DAG
from airflow.sdk.definitions.param import ParamsDict
from clone.config.tasks import TASKS
from clone.tasks.airflow_logic.chain_tasks import chain_tasks
from clone.tasks.airflow_logic.clone_dbt_task import clone_dbt_params


def build_dag(with_dbt: bool = False) -> DAG:
    params = ParamsDict(
        clone_dbt_params(dbt_select="+tag:etablissement") if with_dbt else {}
    )
    return DAG(
        dag_id="test_clone",
        schedule=None,
        start_date=datetime(2024, 1, 1),
        params=params,
    )


class TestChainTasks:

    def test_no_dbt_tasks_without_dbt_params(self):
        dag = build_dag(with_dbt=False)
        chain_tasks(dag)
        assert TASKS.DBT_RUN not in dag.task_ids
        assert TASKS.DBT_TEST not in dag.task_ids

    def test_dbt_tasks_added_with_dbt_params(self):
        dag = build_dag(with_dbt=True)
        chain_tasks(dag)
        assert TASKS.DBT_RUN in dag.task_ids
        assert TASKS.DBT_TEST in dag.task_ids

    def test_dbt_run_runs_before_dbt_test(self):
        dag = build_dag(with_dbt=True)
        chain_tasks(dag)
        dbt_run = dag.get_task(TASKS.DBT_RUN)
        assert TASKS.DBT_TEST in dbt_run.downstream_task_ids

    def test_dbt_run_runs_after_view_switch(self):
        dag = build_dag(with_dbt=True)
        chain_tasks(dag)
        dbt_run = dag.get_task(TASKS.DBT_RUN)
        assert TASKS.OLD_TABLES_REMOVE in dbt_run.upstream_task_ids
