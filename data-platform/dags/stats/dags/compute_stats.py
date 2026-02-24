from airflow.decorators import dag
from airflow.operators.bash import BashOperator
from airflow.sdk.bases.operator import chain
from shared.config.airflow import DEFAULT_ARGS
from shared.config.dbt_commands import DBT_RUN, DBT_TEST
from shared.config.schedules import SCHEDULES
from shared.config.start_dates import START_DATES
from shared.config.tags import TAGS


@dag(
    dag_id="compute_stats",
    default_args=DEFAULT_ARGS,
    schedule=SCHEDULES.EVERY_MONDAY_AT_02_00,
    start_date=START_DATES.DEFAULT,
    dag_display_name="Stats - Rafraîchir les statistiques",
    description=(
        "Ce DAG construit les tables de statistiques en exécutant les modèles dbt "
        "tagués 'stats'."
    ),
    tags=[TAGS.COMPUTE, TAGS.STATS, TAGS.DBT],
    max_active_runs=1,
)
def compute_stats():

    dbt_run_stats = BashOperator(
        task_id="dbt_run_stats",
        bash_command=(f"{DBT_RUN} tag:stats"),
    )
    dbt_test_stats = BashOperator(
        task_id="dbt_test_stats",
        bash_command=(f"{DBT_TEST} tag:stats"),
    )

    chain(
        dbt_run_stats,
        dbt_test_stats,
    )


dag = compute_stats()
