from airflow.providers.standard.operators.python import PythonOperator
from airflow.providers.standard.operators.trigger_dagrun import TriggerDagRunOperator
from airflow.sdk import DagRunState
from airflow.sdk.exceptions import AirflowSkipException


def check_and_trigger(ti, *, target_dag: str) -> None:
    queued_count = ti.get_dr_count(
        dag_id=target_dag,
        states=[DagRunState.QUEUED.value],
    )
    if queued_count > 0:
        raise AirflowSkipException(
            "🔴 Un run est déjà en attente -> on ignore ce trigger"
        )


def should_trigger_dag_task(
    task_id: str,
    target_dag: str,
) -> PythonOperator:
    """publication via Airflow - DBT"""
    return PythonOperator(
        task_id=task_id,
        python_callable=check_and_trigger,
        op_kwargs={"target_dag": target_dag},
    )


def trigger_dag_task(task_id: str, target_dag: str) -> TriggerDagRunOperator:
    """publication via Airflow - DBT"""
    return TriggerDagRunOperator(
        task_id=task_id,
        trigger_dag_id=target_dag,
    )
