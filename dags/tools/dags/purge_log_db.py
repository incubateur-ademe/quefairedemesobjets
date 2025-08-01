"""A Log DB Purge DAG
Use to purge logs of the DB on Scaleway"""

import logging

from airflow import DAG
from airflow.operators.bash import BashOperator
from shared.config.catchups import CATCHUPS
from shared.config.schedules import SCHEDULES
from shared.config.start_dates import START_DATES
from shared.config.tags import TAGS

logger = logging.getLogger(__name__)

with DAG(
    dag_id="purge_log_db",
    dag_display_name="Maintenance - Scaleway - Purger les logs de la DB sur Scaleway",
    schedule=SCHEDULES.HOURLY,
    start_date=START_DATES.YESTERDAY,
    catchup=CATCHUPS.AWLAYS_FALSE,
    is_paused_upon_creation=False,
    max_active_tasks=1,
    tags=[
        TAGS.MAINTENANCE,
        TAGS.NETTOYAGE,
        TAGS.DB,
        TAGS.LOGS,
        TAGS.SCALEWAY,
    ],
) as dag:

    BashOperator(
        task_id="purge_log_db",
        bash_command="cd /opt/airflow/ && scripts/infrastructure/purge_db_logs.sh ",
    )
