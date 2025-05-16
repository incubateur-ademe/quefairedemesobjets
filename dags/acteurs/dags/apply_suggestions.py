from datetime import timedelta

import pendulum
from acteurs.tasks.airflow_logic.db_apply_suggestion_task import (
    db_apply_suggestion_task,
)
from acteurs.tasks.airflow_logic.db_check_suggestion_to_process_task import (
    db_check_suggestion_to_process_task,
)
from acteurs.tasks.airflow_logic.launch_compute_task import (
    launch_compute_acteur_task,
    launch_compute_carte_acteur_task,
)
from airflow.models import DAG

default_args = {
    "owner": "airflow",
    "depends_on_past": False,
    "start_date": pendulum.today("UTC").add(days=-1),
    "retries": 1,
    "retry_delay": timedelta(minutes=5),
}

dag = DAG(
    dag_id="apply_suggestions",
    dag_display_name="Application des suggestions validées",
    default_args=default_args,
    description="traiter les suggestions à traiter",
    tags=["compute", "suggestions", "apply", "acteurs"],
    schedule="*/5 * * * *",
    catchup=False,
    max_active_runs=1,
)


(
    db_check_suggestion_to_process_task(dag)
    >> db_apply_suggestion_task(dag)
    >> launch_compute_carte_acteur_task(dag)
    >> launch_compute_acteur_task(dag)
)
