"""Performs crawl checks on the URLs"""

import logging

from airflow import DAG
from airflow.providers.standard.operators.python import PythonOperator
from airflow.sdk.exceptions import AirflowSkipException
from crawl.config.tasks import TASKS
from crawl.config.xcoms import XCOMS, xcom_pull, xcom_push
from crawl.tasks.business_logic.crawl_urls_check_crawl import crawl_urls_check_crawl

logger = logging.getLogger(__name__)


def task_info_get():
    return f"""


    ============================================================
    Description de la tâche "{TASKS.CHECK_CRAWL}"
    ============================================================

    💡 quoi: on essaye de parcourir les URLs

    🎯 pourquoi: proposer des suggestions à l'étape d'après sur
    les URLs qu'on a réussit à parcourir

    🏗️ comment: avec un crawler python tout simple
    """


def crawl_urls_check_crawl_wrapper(ti, params) -> None:
    logger.info(task_info_get())

    urls_check_crawl = params.get("urls_check_crawl", False)
    if not urls_check_crawl:
        raise AirflowSkipException(f"{urls_check_crawl=}, on s'arrête là")

    df_crawl_diff_standard, df_crawl_diff_other, df_crawl_fail = crawl_urls_check_crawl(
        df=xcom_pull(ti, XCOMS.DF_DNS_OK, skip_if_empty=True),
    )

    xcom_push(ti, XCOMS.DF_CRAWL_DIFF_STANDARD, df_crawl_diff_standard)
    xcom_push(ti, XCOMS.DF_CRAWL_DIFF_OTHER, df_crawl_diff_other)
    xcom_push(ti, XCOMS.DF_CRAWL_FAIL, df_crawl_fail)


def crawl_urls_check_crawl_task(dag: DAG) -> PythonOperator:
    return PythonOperator(
        task_id=TASKS.CHECK_CRAWL,
        python_callable=crawl_urls_check_crawl_wrapper,
        dag=dag,
    )
