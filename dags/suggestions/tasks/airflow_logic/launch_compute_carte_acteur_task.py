from airflow.models import DAG
from airflow.operators.trigger_dagrun import TriggerDagRunOperator


def launch_compute_carte_acteur_task(dag: DAG) -> TriggerDagRunOperator:
    return TriggerDagRunOperator(
        task_id="launch_compute_carte_acteur",
        trigger_dag_id="compute_carte_acteur",
        dag=dag,
    )
