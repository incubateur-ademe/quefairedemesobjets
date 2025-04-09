"""Read data from DB needed for RGPD anonymization"""

import logging

from airflow import DAG
from airflow.exceptions import AirflowSkipException
from airflow.operators.python import PythonOperator
from airflow.utils.trigger_rule import TriggerRule
from enrich.config import DBT, TASKS, XCOMS, xcom_pull
from enrich.tasks.business_logic.enrich_dbt_model_read import (
    enrich_dbt_model_read,
)

logger = logging.getLogger(__name__)


def task_info_get():
    return f"""
    ============================================================
    Description de la tâche "{TASKS.READ_AE_RGPD}"
    ============================================================
    💡 quoi: lecture des données via le modèle DBT
    {DBT.MARTS_ENRICH_AE_RGPD}

    🎯 pourquoi: faire un pré-filtre sur les matches potentiels
    (pas récupérer les ~27M de lignes de la table AE unite_legale)

    🏗️ comment: on récupère uniquement les matches SIREN avec
    des infos de noms/prénoms dans l'AE en passant par de la normalisation
    de chaines de caractères
    """


def enrich_dbt_model_read_wrapper(dbt_model_name, xcom_push_key, ti) -> None:
    logger.info(task_info_get())

    # Config
    config = xcom_pull(ti, XCOMS.CONFIG)
    logger.info(f"📖 Configuration:\n{config.model_dump_json(indent=2)}")

    # Processing
    df = enrich_dbt_model_read(dbt_model_name=dbt_model_name, filters=config.filters)
    if df.empty:
        raise AirflowSkipException("Pas de données DB, on s'arrête là")

    # Result
    ti.xcom_push(key=xcom_push_key, value=df)


def enrich_dbt_model_read_task(
    dag: DAG, task_id: str, dbt_model_name: str, xcom_push_key: str
) -> PythonOperator:
    return PythonOperator(
        task_id=task_id,
        python_callable=enrich_dbt_model_read_wrapper,
        op_args=[dbt_model_name, xcom_push_key],
        dag=dag,
        doc_md=f"**Lecture du modèle DBT**: `{dbt_model_name}`",
        trigger_rule=TriggerRule.ALL_DONE,
    )
