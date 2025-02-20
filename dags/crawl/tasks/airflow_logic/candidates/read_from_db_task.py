import logging

import crawl.tasks.airflow_logic.task_ids as TASK_IDS
from airflow import DAG
from airflow.exceptions import AirflowSkipException
from airflow.operators.python import PythonOperator
from crawl.tasks.business_logic.candidates.read_from_db import (
    crawl_urls_candidates_read_from_db,
)
from utils import logging_utils as log

logger = logging.getLogger(__name__)


def task_info_get(url_type: str):
    return f"""


    ============================================================
    Description de la tâche "{TASK_IDS.READ}"
    ============================================================

    💡 quoi: sélection d'URLs à parcourir dans {url_type}

    🎯 pourquoi: pour pouvoir les parcourir

    🏗️ comment: on va chercher en DB à partir du type d'URL
    """


def crawl_urls_candidates_read_from_db_wrapper(**kwargs) -> None:
    params = kwargs["params"]
    logger.info(task_info_get(params["urls_type"]))

    df = crawl_urls_candidates_read_from_db(params["urls_type"], params["urls_limit"])

    logging.info(log.banner_string("🏁 Résultat final de cette tâche"))
    log.preview_df_as_markdown("URLs à parcourir", df)

    if df.empty:
        raise AirflowSkipException("Pas d'URLs à parcourir = on s'arrête là")

    kwargs["ti"].xcom_push(key="df", value=df)


def crawl_urls_candidates_read_from_db_task(dag: DAG) -> PythonOperator:
    return PythonOperator(
        task_id=TASK_IDS.READ,
        python_callable=crawl_urls_candidates_read_from_db_wrapper,
        dag=dag,
    )
