"""Performs crawl checks on the URLs"""

import logging

from airflow import DAG
from airflow.operators.python import PythonOperator
from clone.config import DIR_SQL_VALIDATION, TASKS, XCOMS, CloneConfig, xcom_pull
from clone.tasks.business_logic.clone_table_validate import clone_table_validate

from utils import logging_utils as log

logger = logging.getLogger(__name__)


def task_info_get(config: CloneConfig) -> str:
    return f"""
    ============================================================
    Description de la tâche "{TASKS.TABLE_VALIDATE}"
    ============================================================
    💡 quoi: valider la table {config.table_name}

    🎯 pourquoi: s'assurer que l'ingestion est OK un minimum

    🏗️ comment: en rejouant les requêtes présentes dans
    {DIR_SQL_VALIDATION / config.table_kind} sur la table
    créée précédemment
    """


def clone_table_validate_wrapper(ti) -> None:

    config: CloneConfig = xcom_pull(ti, XCOMS.CONFIG)

    logger.info(task_info_get(config))
    log.preview("Configuration", config.model_dump())

    clone_table_validate(
        table_kind=config.table_kind,
        table_name=config.table_name,
        dry_run=config.dry_run,
    )


def clone_table_validate_task(dag: DAG) -> PythonOperator:
    return PythonOperator(
        task_id=TASKS.TABLE_VALIDATE,
        python_callable=clone_table_validate_wrapper,
        dag=dag,
    )
