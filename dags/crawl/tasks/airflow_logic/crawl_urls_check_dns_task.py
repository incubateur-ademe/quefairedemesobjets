"""Performs DNS checks on the domains of the URLs"""

import logging

from airflow import DAG
from airflow.operators.python import PythonOperator
from crawl.config.tasks import TASKS
from crawl.config.xcoms import XCOMS, xcom_pull
from crawl.tasks.business_logic.crawl_urls_check_dns import crawl_urls_check_dns

logger = logging.getLogger(__name__)


def task_info_get():
    return f"""


    ============================================================
    Description de la tâche "{TASKS.CHECK_DNS}"
    ============================================================

    💡 quoi: on essaye de résoudre les noms de domaines

    🎯 pourquoi: aucune raison d'essayer de parcourir les
    URLs si on arrive même pas à atteindre leur domaine

    🏗️ comment: pour chaque groupe d'URLs, on compile une
    liste unique de domaines qu'on essaye de résoudre et
    on retourn 2 dataframes:
     - df_dns_ok : les domaines qu'on a réussi à résoudre
     - df_dns_fail : les domaines qu'on a pas réussi à résoudre

    Si df_dns_ok est vide on s'arrête là
    """


def crawl_urls_check_dns_wrapper(ti) -> None:
    logger.info(task_info_get())

    df_dns_ok, df_dns_fail = crawl_urls_check_dns(
        df=xcom_pull(ti, XCOMS.DF_SYNTAX_OK, skip_if_empty=True),
    )

    ti.xcom_push(key=XCOMS.DF_DNS_OK, value=df_dns_ok)
    ti.xcom_push(key=XCOMS.DF_DNS_FAIL, value=df_dns_fail)


def crawl_urls_check_dns_task(dag: DAG) -> PythonOperator:
    return PythonOperator(
        task_id=TASKS.CHECK_DNS,
        python_callable=crawl_urls_check_dns_wrapper,
        dag=dag,
    )
