"""Performs crawl checks on the URLs"""

import logging

from airflow import DAG
from airflow.operators.python import PythonOperator
from crawl.config import tasks as TASKS
from crawl.config.xcom import (
    XCOM_DF_DNS_OK,
    XCOM_DF_URLS_FAIL,
    XCOM_DF_URLS_OK_DIFF,
    XCOM_DF_URLS_OK_SAME,
    xcom_pull,
)
from crawl.tasks.business_logic.crawl_urls_check_urls import crawl_urls_check_reach

logger = logging.getLogger(__name__)


def task_info_get():
    return f"""


    ============================================================
    Description de la tâche "{TASKS.CHECK_URLS}"
    ============================================================

    💡 quoi: on essaye de parcourir les URLs

    🎯 pourquoi: proposer des suggestions à l'étape d'après sur
    les URLs qu'on a réussit à parcourir

    🏗️ comment: avec un crawler python tout simple
    """


def crawl_urls_check_reach_wrapper(ti) -> None:
    logger.info(task_info_get())

    df_urls_ok_same, df_urls_ok_diff, df_urls_fail = crawl_urls_check_reach(
        df=xcom_pull(ti, XCOM_DF_DNS_OK),
    )

    ti.xcom_push(key=XCOM_DF_URLS_OK_SAME, value=df_urls_ok_same)
    ti.xcom_push(key=XCOM_DF_URLS_OK_DIFF, value=df_urls_ok_diff)
    ti.xcom_push(key=XCOM_DF_URLS_FAIL, value=df_urls_fail)


def crawl_urls_check_reach_task(dag: DAG) -> PythonOperator:
    return PythonOperator(
        task_id=TASKS.CHECK_URLS,
        python_callable=crawl_urls_check_reach_wrapper,
        dag=dag,
    )
