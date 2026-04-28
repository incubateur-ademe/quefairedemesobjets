"""A Log DB Purge DAG
Use to purge logs of the DB on Scaleway"""

from airflow.providers.standard.operators.bash import BashOperator
from airflow.sdk import dag
from shared.config.schedules import SCHEDULES
from shared.config.start_dates import START_DATES
from shared.config.tags import TAGS


@dag(
    dag_id="purge_log_db",
    dag_display_name="Maintenance - Scaleway - Purger les logs de la DB sur Scaleway",
    schedule=SCHEDULES.EVERY_HOUR_AT_MIN_3,
    start_date=START_DATES.DEFAULT,
    is_paused_upon_creation=False,
    max_active_tasks=1,
    tags=[
        TAGS.MAINTENANCE,
        TAGS.NETTOYAGE,
        TAGS.DB,
        TAGS.LOGS,
        TAGS.SCALEWAY,
    ],
)
def purge_log_db():
    BashOperator(
        task_id="purge_log_db",
        # Trailing space prevents Airflow from interpreting the command as a
        # path to a Jinja template file (BashOperator.template_ext = ('.sh',)).
        bash_command="/opt/airflow/scripts/infrastructure/purge_db_logs.sh ",
    )


purge_log_db()
