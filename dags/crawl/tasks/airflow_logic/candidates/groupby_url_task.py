import logging

import crawl.tasks.airflow_logic.task_ids as TASK_IDS
from airflow import DAG
from airflow.operators.python import PythonOperator
from crawl.tasks.business_logic.candidates.groupby_url import (
    crawl_urls_candidates_groupby_url,
)
from utils import logging_utils as log

logger = logging.getLogger(__name__)


def task_info_get():
    return f"""


    ============================================================
    Description de la tâche "{TASK_IDS.GROUPBY_URL}"
    ============================================================

    💡 quoi: regroupement par URL

    🎯 pourquoi: pas faire un doublon de travail, on traite
    par URL et non pas par entrée (ex: acteurs)

    🏗️ comment: on groupe par URL et aggrège toutes les entrées
    associées (ex: acteurs) pour générer des suggestions pour
    toute ces entrées plus tard
    """


def crawl_urls_candidates_groupby_url_wrapper(**kwargs) -> None:
    logger.info(task_info_get())

    df = kwargs["ti"].xcom_pull(key="df", task_ids=TASK_IDS.READ)
    df = crawl_urls_candidates_groupby_url(
        df, col_groupby="url_original", col_grouped_data="acteurs"
    )

    logging.info(log.banner_string("🏁 Résultat final de cette tâche"))
    log.preview_df_as_markdown("URLs regroupées", df)

    if df.empty:
        raise ValueError("Si est on arrivé ici, on devrait avoir des URLs")

    kwargs["ti"].xcom_push(key="df", value=df)


def crawl_urls_candidates_groupby_url_task(dag: DAG) -> PythonOperator:
    return PythonOperator(
        task_id=TASK_IDS.GROUPBY_URL,
        python_callable=crawl_urls_candidates_groupby_url_wrapper,
        dag=dag,
    )
