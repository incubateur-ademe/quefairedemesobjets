"""Generate suggestions for enrichment DAGs"""

import logging
from typing import Any

from airflow import DAG
from airflow.models.taskinstance import TaskInstance
from airflow.providers.standard.operators.python import PythonOperator
from airflow.sdk.exceptions import AirflowSkipException
from airflow.task.trigger_rule import TriggerRule
from enrich.config.models import EnrichActeursClosedConfig
from enrich.tasks.business_logic.enrich_dbt_model_suggest import (
    enrich_dbt_model_suggest,
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


def enrich_dbt_model_suggest_wrapper(
    task_id: str,
    cohort: str,
    dbt_model_name: str,
    ti: TaskInstance,
    params: dict[str, Any],
    dag: DAG,
) -> None:
    logger.info(task_info_get(task_id, dbt_model_name))

    # Config
    config = EnrichActeursClosedConfig(**params)
    logger.info(f"📖 Configuration:\n{config.model_dump_json(indent=2)}")

    # Processing
    suggestions_written = enrich_dbt_model_suggest(
        dbt_model_name=dbt_model_name,
        filters=config.filters,
        cohort=cohort,
        identifiant_action=dag.dag_id,
        dry_run=config.dry_run,
    )
    if not suggestions_written:
        raise AirflowSkipException("Pas de suggestions écrites")


def enrich_dbt_model_suggest_task(
    dag: DAG,
    task_id: str,
    cohort: str,
    dbt_model_name: str,
) -> PythonOperator:
    return PythonOperator(
        task_id=task_id,
        python_callable=enrich_dbt_model_suggest_wrapper,
        op_args=[task_id, cohort, dbt_model_name],
        dag=dag,
        doc_md=f"**Suggestions** pour la cohorte: **{cohort}**",
        trigger_rule=TriggerRule.ALL_DONE,
    )
