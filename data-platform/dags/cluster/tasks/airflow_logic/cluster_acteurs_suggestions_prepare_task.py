import logging

import pandas as pd
from airflow import DAG
from airflow.providers.standard.operators.python import PythonOperator
from cluster.config.tasks import TASKS
from cluster.config.xcoms import XCOMS, xcom_pull
from cluster.tasks.business_logic.cluster_acteurs_suggestions.prepare import (
    cluster_acteurs_suggestions_prepare,
)
from utils import logging_utils as log

logger = logging.getLogger(__name__)


def task_info_get():
    return f"""


    ============================================================
    Description de la tâche "{TASKS.SUGGESTIONS_PREPARE}"
    ============================================================

    💡 quoi: affichage de l'état final des suggestions avant
    écriture en base

    🎯 pourquoi: avoir une vue d'ensemble au niveau airflow:
     - si on utilise le dry_un avant écriture
     - si quelque se passe mal au niveau de l'écriture en base

    🏗️ comment: pas de nouvelle données générées ici, on reprends
    juste les données des tâches précédentes qu'on essaye d'afficher
    de manière lisible
    """


def cluster_acteurs_suggestions_prepare_wrapper(ti) -> None:
    logger.info(task_info_get())

    df: pd.DataFrame = xcom_pull(ti, XCOMS.DF_PARENTS_CHOOSE_DATA)
    if "acteur_type" in df.columns:
        df["acteur_type"] = df["acteur_type"].astype("Int64")
    log.preview("df after cast", df)

    if df.empty:
        raise ValueError("Pas de clusters récupérés, on ne devrait pas être là")

    working, failing = cluster_acteurs_suggestions_prepare(df)
    ti.xcom_push(key=XCOMS.SUGGESTIONS_WORKING, value=working)
    ti.xcom_push(key=XCOMS.SUGGESTIONS_FAILING, value=failing)


def cluster_acteurs_suggestions_prepare_task(dag: DAG) -> PythonOperator:
    return PythonOperator(
        task_id=TASKS.SUGGESTIONS_PREPARE,
        python_callable=cluster_acteurs_suggestions_prepare_wrapper,
        dag=dag,
    )
