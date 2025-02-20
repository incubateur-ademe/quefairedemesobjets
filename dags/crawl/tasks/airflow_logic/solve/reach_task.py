import logging

import pandas as pd
from airflow import DAG
from airflow.exceptions import AirflowSkipException
from airflow.operators.python import PythonOperator
from crawl.tasks.airflow_logic import task_ids as TASK_IDS
from crawl.tasks.business_logic.solve.reach import crawl_urls_solve_reach
from utils import logging_utils as log

logger = logging.getLogger(__name__)


def task_info_get():
    return f"""


    ============================================================
    Description de la tâche "{TASK_IDS.SOLVE_REACH}"
    ============================================================

    💡 quoi: on essaye de parcourir les URLs

    🎯 pourquoi: proposer des suggestions à l'étape d'après sur
    les URLs qu'on a réussit à parcourir

    🏗️ comment: avec un crawler python tout simple
    """


def crawl_urls_solve_reach_wrapper(**kwargs) -> None:
    logger.info(task_info_get())

    df = kwargs["ti"].xcom_pull(key="df", task_ids=TASK_IDS.SOLVE_SYNTAX)
    if not isinstance(df, pd.DataFrame) or df.empty:
        msg = f"df de {TASK_IDS.SOLVE_SYNTAX} vide: on devrait pas être ici"
        raise ValueError(msg)

    log.preview_df_as_markdown("🟢 URLs qu'on va essayer de parcourir", df)
    df_ok_same, df_ok_diff, df_fail = crawl_urls_solve_reach(df)

    logging.info(log.banner_string("🏁 Résultat final de cette tâche"))
    log.preview_df_as_markdown("🟢 URLs en succès ET inchangées", df_ok_same)
    log.preview_df_as_markdown("🟡 URLs en succès ET différentes", df_ok_diff)
    log.preview_df_as_markdown("🔴 URLs en échec", df_fail)

    if df_ok_diff.empty and df_fail.empty:
        msg = "0️⃣ Pas d'URLs en succès diff/échec = pas de suggestions"
        raise AirflowSkipException(msg)

    kwargs["ti"].xcom_push(key="df_ok_same", value=df_ok_same)
    kwargs["ti"].xcom_push(key="df_ok_diff", value=df_ok_diff)
    kwargs["ti"].xcom_push(key="df_fail", value=df_fail)


def crawl_urls_solve_reach_task(dag: DAG) -> PythonOperator:
    return PythonOperator(
        task_id=TASK_IDS.SOLVE_REACH,
        python_callable=crawl_urls_solve_reach_wrapper,
        dag=dag,
    )
