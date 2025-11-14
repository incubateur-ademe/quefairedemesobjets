from datetime import timedelta

from airflow.models import DAG
from shared.config.schedules import SCHEDULES
from shared.config.start_dates import START_DATES
from shared.config.tags import TAGS
from suggestions.tasks.airflow_logic.db_apply_suggestion_task import (
    db_apply_suggestion_task,
)
from suggestions.tasks.airflow_logic.db_check_suggestion_to_process_task import (
    db_check_suggestion_to_process_task,
)
from suggestions.tasks.airflow_logic.trigger_compute_acteur_task import (
    should_trigger_compute_acteur_task,
    trigger_compute_acteur_task,
)

default_args = {
    "owner": "airflow",
    "depends_on_past": False,
    "retries": 1,
    "retry_delay": timedelta(minutes=5),
}

dag = DAG(
    dag_id="apply_suggestions",
    dag_display_name="Acteurs - Application des suggestions validées",
    default_args=default_args,
    schedule=SCHEDULES.EVERY_5_MINUTES,
    start_date=START_DATES.DEFAULT,
    description="traiter les suggestions à traiter",
    tags=[TAGS.COMPUTE, TAGS.SUGGESTIONS, TAGS.APPLY, TAGS.ACTEURS],
    max_active_runs=1,
)


(
    db_check_suggestion_to_process_task(dag)
    >> db_apply_suggestion_task(dag)
    >> should_trigger_compute_acteur_task(dag)
    >> trigger_compute_acteur_task(dag)
)
