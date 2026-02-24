from airflow.decorators import dag
from airflow.sdk.bases.operator import chain
from shared.config.airflow import DEFAULT_ARGS
from shared.config.schedules import SCHEDULES
from shared.config.start_dates import START_DATES
from shared.config.tags import TAGS
from shared.tasks.airflow_logic.trigger_dag_task import (
    should_trigger_dag_task,
    trigger_dag_task,
)
from suggestions.tasks.airflow_logic.db_apply_suggestion_task import (
    db_apply_suggestion_task,
)
from suggestions.tasks.airflow_logic.db_check_suggestion_to_process_task import (
    db_check_suggestion_to_process_task,
)


@dag(
    dag_id="apply_suggestions_groupe",
    dag_display_name=(
        "Acteurs - [NEW VERSION] - Application des suggestions groupées validées"
    ),
    default_args=DEFAULT_ARGS,
    schedule=SCHEDULES.EVERY_5_MINUTES,
    start_date=START_DATES.DEFAULT,
    description="traiter les suggestions à traiter",
    tags=[TAGS.COMPUTE, TAGS.SUGGESTIONS, TAGS.APPLY, TAGS.ACTEURS],
    max_active_runs=1,
)
def apply_suggestions():
    chain(
        db_check_suggestion_to_process_task(use_suggestion_groupe=True),
        db_apply_suggestion_task(use_suggestion_groupe=True),
        should_trigger_dag_task(
            task_id="check_dag_state",
            target_dag="compute_acteurs",
        ),
        trigger_dag_task(
            task_id="launch_compute_acteurs",
            target_dag="compute_acteurs",
        ),
    )


dag = apply_suggestions()
