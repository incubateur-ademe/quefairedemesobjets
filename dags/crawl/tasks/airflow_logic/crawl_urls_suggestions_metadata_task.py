"""Generates metadata for the suggestions
based on previous check tasks. If no suggestions,
then metadata is None and we skip the rest of pipeline.

Given we have already 3 types of checks (syntax, DNS, crawl),
might decide to add more (e.g. ping before crawl) we thought
it was easier to just always reach the metadata phase and
decide to skip or not rather than manage complex task dependencies"""

import logging

import crawl.config.tasks as TASKS
from airflow import DAG
from airflow.exceptions import AirflowSkipException
from airflow.operators.python import PythonOperator
from crawl.config.constants import (
    SCENARIO_DNS_FAIL,
    SCENARIO_SYNTAX_FAIL,
    SCENARIO_URL_FAIL,
    SCENARIO_URL_OK_DIFF,
)
from crawl.config.xcom import (
    XCOM_DF_DNS_FAIL,
    XCOM_DF_SYNTAX_FAIL,
    XCOM_DF_URLS_FAIL,
    XCOM_DF_URLS_OK_DIFF,
    XCOM_SUGGESTIONS_META,
    xcom_pull,
)
from crawl.tasks.business_logic.crawl_urls_suggestions_metadata import (
    crawl_urls_suggestions_metadata,
)

logger = logging.getLogger(__name__)


def task_info_get():
    return f"""


    ============================================================
    Description de la tâche "{TASKS.SUGGESTIONS_META}"
    ============================================================

    💡 quoi: metadata pour la cohorte de suggestions à venir,
    si 0 suggestions, on s'arrête là

    🎯 pourquoi: avoir une vue d'ensemble des suggestions
    avant de les préparer

    🏗️ comment: calculs du nombre d'URLS & acteurs pour chacun
    des scénarios suivants:
        - {SCENARIO_SYNTAX_FAIL}
        - {SCENARIO_DNS_FAIL}
        - {SCENARIO_URL_FAIL}
        - {SCENARIO_URL_OK_DIFF}
    """


def crawl_urls_suggestions_metadata_wrapper(ti) -> None:
    logger.info(task_info_get())

    metadata = crawl_urls_suggestions_metadata(
        df_syntax_fail=xcom_pull(ti, XCOM_DF_SYNTAX_FAIL),
        df_dns_fail=xcom_pull(ti, XCOM_DF_DNS_FAIL),
        df_urls_ok_diff=xcom_pull(ti, XCOM_DF_URLS_OK_DIFF),
        df_urls_fail=xcom_pull(ti, XCOM_DF_URLS_FAIL),
    )

    if metadata is None:
        raise AirflowSkipException("Metadata = 0 suggestions, on s'arrête là")

    ti.xcom_push(key=XCOM_SUGGESTIONS_META, value=metadata)


def crawl_urls_suggestions_metadata_task(dag: DAG) -> PythonOperator:
    return PythonOperator(
        task_id=TASKS.SUGGESTIONS_META,
        python_callable=crawl_urls_suggestions_metadata_wrapper,
        dag=dag,
    )
