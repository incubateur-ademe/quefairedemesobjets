from airflow.exceptions import AirflowSkipException
from airflow.models import DAG, DagRun
from airflow.operators.python import PythonOperator
from airflow.operators.trigger_dagrun import TriggerDagRunOperator
from airflow.utils.session import provide_session
from airflow.utils.state import State

TARGET_DAG = "compute_acteurs"
TRIGGERED_TASK_ID = "launch_compute_acteurs"


@provide_session
def should_trigger(session=None):
    if session is None:
        return True
    # should be triggered if no dag is queued
    return (
        session.query(DagRun)
        .filter(DagRun.dag_id == TARGET_DAG, DagRun.state == State.QUEUED)
        .count()
        == 0
    )


def check_and_trigger(**context):
    if not should_trigger():
        raise AirflowSkipException(
            "🔴 Un run est déjà en attente -> on ignore ce trigger"
        )
    return TRIGGERED_TASK_ID


def should_trigger_compute_acteur_task(dag: DAG) -> PythonOperator:
    """publication via Airflow - DBT"""
    return PythonOperator(
        task_id="check_dag_state",
        python_callable=check_and_trigger,
    )


def trigger_compute_acteur_task(dag: DAG) -> TriggerDagRunOperator:
    """publication via Airflow - DBT"""
    return TriggerDagRunOperator(
        task_id=TRIGGERED_TASK_ID,
        trigger_dag_id=TARGET_DAG,
        dag=dag,
    )
