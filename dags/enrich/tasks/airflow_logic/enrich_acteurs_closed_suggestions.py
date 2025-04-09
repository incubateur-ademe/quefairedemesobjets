"""Read data from DB needed for RGPD anonymization"""

import logging

from airflow import DAG
from airflow.models.taskinstance import TaskInstance
from airflow.operators.python import PythonOperator
from enrich.config import XCOMS, xcom_pull
from enrich.tasks.business_logic.enrich_acteurs_closed_suggestions import (
    enrich_acteurs_closed_suggestions,
)

logger = logging.getLogger(__name__)


def task_info_get(task_id, df_xcom_key):
    return f"""
    ============================================================
    Description de la tâche "{task_id}"
    ============================================================
    💡 quoi: on génère les suggestions à partir de la df
    {df_xcom_key}

    🎯 pourquoi: le but de ce DAG

    🏗️ comment: pour chaque acteur fermé, on génère 1 suggestion
    """


def enrich_acteurs_closed_suggestions_wrapper(
    cohort_type: str, df_xcom_key: str, task_id: str, ti: TaskInstance, dag: DAG
) -> None:
    logger.info(task_info_get(task_id, df_xcom_key))

    # Config
    config = xcom_pull(ti, XCOMS.CONFIG)
    logger.info(f"📖 Configuration:\n{config.model_dump_json(indent=2)}")

    # Processing
    enrich_acteurs_closed_suggestions(
        df=xcom_pull(ti, df_xcom_key),
        cohort_type=cohort_type,
        identifiant_action=dag.dag_id,
        dry_run=config.dry_run,
    )


def enrich_acteurs_closed_suggestions_task(
    dag: DAG, task_id: str, cohort_type: str, df_xcom_key: str
) -> PythonOperator:
    return PythonOperator(
        task_id=task_id,
        python_callable=enrich_acteurs_closed_suggestions_wrapper,
        op_args=[cohort_type, df_xcom_key, task_id],
        dag=dag,
        doc_md=f"**Suggestions** pour la cohorte: {cohort_type}**",
    )
