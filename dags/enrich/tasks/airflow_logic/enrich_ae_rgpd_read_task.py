"""Read data from DB needed for RGPD anonymization"""

import logging

from airflow import DAG
from airflow.exceptions import AirflowSkipException
from airflow.operators.python import PythonOperator
from enrich.config import DBT, TASKS, XCOMS
from enrich.tasks.business_logic.enrich_ae_rgpd_read import (
    enrich_ae_rgpd_read,
)

logger = logging.getLogger(__name__)


def task_info_get():
    return f"""
    ============================================================
    Description de la tâche "{TASKS.READ}"
    ============================================================
    💡 quoi: lecture des données via le modèle DBT
    {DBT.MARTS_ENRICH_AE_RGPD}

    🎯 pourquoi: faire un pré-filtre sur les matches potentiels
    (pas récupérer les ~27M de lignes de la table AE unite_legale)

    🏗️ comment: on récupère uniquement les matches SIREN avec
    des infos de noms/prénoms dans l'AE en passant par de la normalisation
    de chaines de caractères
    """


def enrich_ae_rgpd_read_wrapper(ti, params) -> None:
    logger.info(task_info_get())

    df = enrich_ae_rgpd_read(
        dbt_model_name=DBT.MARTS_ENRICH_AE_RGPD,
        filter_comments_contain=params["filter_comments_contain"],
    )
    if df.empty:
        raise AirflowSkipException("Pas de données DB, on s'arrête là")

    ti.xcom_push(key=XCOMS.DF_READ, value=df)


def enrich_ae_rgpd_read_task(dag: DAG) -> PythonOperator:
    return PythonOperator(
        task_id=TASKS.READ,
        python_callable=enrich_ae_rgpd_read_wrapper,
        dag=dag,
    )
