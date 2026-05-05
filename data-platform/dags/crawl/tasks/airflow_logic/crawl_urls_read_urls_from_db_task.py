"""Reads URLs & acteur data from DB whilst
grouping by URL so we don't repeat URL checks
unnecessarily"""

import logging

from airflow import DAG
from airflow.providers.standard.operators.python import PythonOperator
from airflow.sdk.exceptions import AirflowSkipException
from crawl.config.tasks import TASKS
from crawl.config.xcoms import XCOMS, xcom_push
from crawl.tasks.business_logic.crawl_urls_read_urls_from_db import (
    crawl_urls_read_urls_from_db,
)

logger = logging.getLogger(__name__)


def task_info_get():
    return f"""


    ============================================================
    Description de la tâche "{TASKS.READ}"
    ============================================================

    💡 quoi: sélection d'URLs à parcourir

    🎯 pourquoi: pour pouvoir les parcourir

    🏗️ comment: on va chercher en DB à partir du type d'URL
    """


def crawl_urls_read_urls_from_db_wrapper(ti, params) -> None:
    logger.info(task_info_get())

    df = crawl_urls_read_urls_from_db(limit=params["urls_limit"])

    if df.empty:
        raise AirflowSkipException("Pas d'URLs à parcourir = on s'arrête là")

    xcom_push(ti, XCOMS.DF_READ, df)


def crawl_urls_read_urls_from_db_task(dag: DAG) -> PythonOperator:
    return PythonOperator(
        task_id=TASKS.READ,
        python_callable=crawl_urls_read_urls_from_db_wrapper,
        dag=dag,
    )
