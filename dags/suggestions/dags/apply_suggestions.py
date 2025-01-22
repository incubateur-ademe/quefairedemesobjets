from datetime import timedelta

from airflow.models import DAG
from airflow.utils.dates import days_ago
from suggestions.tasks.airflow_logic import (
    db_normalize_suggestion_task,
    db_read_suggestiontoprocess_task,
    db_write_validsuggestions_task,
    launch_compute_carte_acteur_task,
)

default_args = {
    "owner": "airflow",
    "depends_on_past": False,
    "start_date": days_ago(1),
    "retries": 1,
    "retry_delay": timedelta(minutes=5),
}

dag = DAG(
    dag_id="apply_suggestions",
    dag_display_name="Application des suggestions validées",
    default_args=default_args,
    description="traiter les suggestions à traiter",
    schedule="*/5 * * * *",
    catchup=False,
    max_active_runs=1,
)


(
    db_read_suggestiontoprocess_task(dag)
    >> db_normalize_suggestion_task(dag)
    >> db_write_validsuggestions_task(dag)
    >> launch_compute_carte_acteur_task(dag)
)
