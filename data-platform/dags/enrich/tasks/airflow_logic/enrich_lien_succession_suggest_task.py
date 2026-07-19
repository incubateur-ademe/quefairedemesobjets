"""Generate grouped lien succession suggestions for the enrich DAG"""

import logging
from typing import Any

from airflow import DAG
from airflow.models.taskinstance import TaskInstance
from airflow.providers.standard.operators.python import PythonOperator
from airflow.sdk.exceptions import AirflowSkipException
from airflow.task.trigger_rule import TriggerRule
from enrich.config.models import EnrichActeursLienSuccessionConfig
from enrich.tasks.business_logic.enrich_lien_succession_suggest import (
    enrich_lien_succession_suggest,
)

logger = logging.getLogger(__name__)


def enrich_lien_succession_suggest_wrapper(
    task_id: str,
    cohort: str,
    dbt_model_name: str,
    suggest_action: str,
    ti: TaskInstance,
    params: dict[str, Any],
    dag: DAG,
) -> None:
    logger.info(f"Tâche {task_id}: génération des suggestions {cohort}")

    config = EnrichActeursLienSuccessionConfig(**params)
    logger.info(f"📖 Configuration:\n{config.model_dump_json(indent=2)}")

    suggestions_written = enrich_lien_succession_suggest(
        dbt_model_name=dbt_model_name,
        cohort=cohort,
        suggest_action=suggest_action,
        identifiant_action=dag.dag_id,
        dry_run=config.dry_run,
    )
    if not suggestions_written:
        raise AirflowSkipException("Pas de suggestions écrites")


def enrich_lien_succession_suggest_task(
    dag: DAG,
    task_id: str,
    cohort: str,
    dbt_model_name: str,
    suggest_action: str,
) -> PythonOperator:
    return PythonOperator(
        task_id=task_id,
        python_callable=enrich_lien_succession_suggest_wrapper,
        op_args=[
            task_id,
            cohort,
            dbt_model_name,
            suggest_action,
        ],
        dag=dag,
        doc_md=f"**Suggestions groupées** pour la cohorte: **{cohort}**",
        trigger_rule=TriggerRule.ALL_DONE,
    )
