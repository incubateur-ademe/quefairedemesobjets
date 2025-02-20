import logging

import crawl.tasks.airflow_logic.task_ids as TASK_IDS
from airflow import DAG
from airflow.operators.python import PythonOperator
from crawl.tasks.business_logic.suggestions.metadata import (
    crawl_urls_suggestions_metadata,
)

logger = logging.getLogger(__name__)


def task_info_get():
    return f"""


    ============================================================
    Description de la tâche "{TASK_IDS.SUGGESTIONS_METADATA}"
    ============================================================

    💡 quoi: metadata pour la cohorte de suggestions à venir

    🎯 pourquoi: avoir une vue d'ensemble des suggestions

    🏗️ comment: calculs sur la base des URLS & acteurs:
        - 🟢 En succès ET inchangées = pas de suggestion
        - 🟡 En succès ET différentes = suggestion de la nouvelle URL
        - 🔴 En échec = suggestion de EMPTY
    """


def crawl_urls_suggestions_metadata_wrapper(**kwargs) -> None:
    logger.info(task_info_get())

    df_ok_same = kwargs["ti"].xcom_pull(key="df_ok_same", task_ids=TASK_IDS.SOLVE_REACH)
    df_ok_diff = kwargs["ti"].xcom_pull(key="df_ok_diff", task_ids=TASK_IDS.SOLVE_REACH)
    df_fail = kwargs["ti"].xcom_pull(key="df_fail", task_ids=TASK_IDS.SOLVE_REACH)
    metadata = crawl_urls_suggestions_metadata(
        df_ok_same=df_ok_same, df_ok_diff=df_ok_diff, df_fail=df_fail
    )
    kwargs["ti"].xcom_push(key="metadata", value=metadata)


def crawl_urls_suggestions_metadata_task(dag: DAG) -> PythonOperator:
    return PythonOperator(
        task_id=TASK_IDS.SUGGESTIONS_METADATA,
        python_callable=crawl_urls_suggestions_metadata_wrapper,
        dag=dag,
    )
