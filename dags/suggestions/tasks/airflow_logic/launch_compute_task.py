from airflow.models import DAG
from airflow.operators.trigger_dagrun import TriggerDagRunOperator


def launch_compute_acteur_task(dag: DAG) -> TriggerDagRunOperator:
    """publication via Airflow - DBT"""
    return TriggerDagRunOperator(
        task_id="launch_compute_acteurs",
        trigger_dag_id="compute_acteurs",
        dag=dag,
    )
