"""Reads URLs & acteur data from DB whilst
grouping by URL so we don't repeat URL checks
unnecessarily"""

import logging

import crawl.config.tasks as TASKS
from airflow import DAG
from airflow.exceptions import AirflowSkipException
from airflow.operators.python import PythonOperator
from crawl.config.xcom import XCOM_DF_READ
from crawl.tasks.business_logic.crawl_urls_read_from_db import (
    crawl_urls_candidates_read_from_db,
)

logger = logging.getLogger(__name__)


def task_info_get(url_type: str):
    return f"""


    ============================================================
    Description de la tâche "{TASKS.READ}"
    ============================================================

    💡 quoi: sélection d'URLs à parcourir dans {url_type}

    🎯 pourquoi: pour pouvoir les parcourir

    🏗️ comment: on va chercher en DB à partir du type d'URL
    """


def crawl_urls_candidates_read_from_db_wrapper(ti, params) -> None:
    logger.info(task_info_get(params["urls_type"]))

    df = crawl_urls_candidates_read_from_db(
        url_type=params["urls_type"],
        limit=params["urls_limit"],
    )

    if df.empty:
        raise AirflowSkipException("Pas d'URLs à parcourir = on s'arrête là")

    ti.xcom_push(key=XCOM_DF_READ, value=df)


def crawl_urls_candidates_read_from_db_task(dag: DAG) -> PythonOperator:
    return PythonOperator(
        task_id=TASKS.READ,
        python_callable=crawl_urls_candidates_read_from_db_wrapper,
        dag=dag,
    )
