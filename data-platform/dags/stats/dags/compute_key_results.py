from airflow.sdk import dag, task
from shared.config.airflow import DEFAULT_ARGS
from shared.config.schedules import SCHEDULES
from shared.config.start_dates import START_DATES
from shared.config.tags import TAGS


@dag(
    dag_id="compute_key_results",
    default_args=DEFAULT_ARGS,
    schedule=SCHEDULES.EVERY_DAY_AT_01_00,
    start_date=START_DATES.DEFAULT,
    dag_display_name="Stats - Calculer les key results",
    description=(
        "Calcule les key results définis dans webapp/stats/key_results.py "
        "(PostHog, ORM) et les enregistre pour Metabase."
    ),
    tags=[TAGS.COMPUTE, TAGS.STATS],
    max_active_runs=1,
)
def compute_key_results():
    @task
    def compute() -> int:
        from utils.django import django_setup_full

        django_setup_full()

        from stats.key_results import compute_all

        return compute_all()

    compute()


dag = compute_key_results()
