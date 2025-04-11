from airflow.models import DAG
from airflow.operators.trigger_dagrun import TriggerDagRunOperator


def launch_compute_carte_acteur_task(dag: DAG) -> TriggerDagRunOperator:
    """publication via Airflow - python"""
    return TriggerDagRunOperator(
        task_id="launch_compute_carte_acteur",
        trigger_dag_id="compute_carte_acteur",
        dag=dag,
    )


def launch_compute_acteur_task(dag: DAG) -> TriggerDagRunOperator:
    """publication via Airflow - DBT"""
    return TriggerDagRunOperator(
        task_id="launch_compute_acteurs",
        trigger_dag_id="compute_acteurs",
        dag=dag,
    )
