from airflow.exceptions import AirflowSkipException
from airflow.models import DagRun
from airflow.operators.python import PythonOperator
from airflow.operators.trigger_dagrun import TriggerDagRunOperator
from airflow.utils.session import provide_session
from airflow.utils.state import State


@provide_session
def should_trigger(session=None, *, target_dag: str) -> bool:
    if session is None:
        return True
    # should be triggered if no dag is queued
    return (
        session.query(DagRun)
        .filter(DagRun.dag_id == target_dag, DagRun.state == State.QUEUED)
        .count()
        == 0
    )


def check_and_trigger(ti, params, *, target_dag: str) -> None:
    if not should_trigger(target_dag=target_dag):
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
