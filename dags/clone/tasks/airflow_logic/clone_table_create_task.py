"""Performs crawl checks on the URLs"""

import logging

from airflow import DAG
from airflow.operators.python import PythonOperator
from clone.config import TASKS, XCOMS, CloneConfig, xcom_pull
from clone.tasks.business_logic.clone_table_create import clone_ae_table_create
from utils import logging_utils as log

logger = logging.getLogger(__name__)


def task_info_get(config: CloneConfig) -> str:
    return f"""
    ============================================================
    Description de la tâche "{TASKS.TABLE_CREATE}"
    ============================================================
    💡 quoi: créer la table {config.table_kind} ({config.table_name})
    à partir de {config.data_url}

    🎯 pourquoi: c'est le but de ce DAG, pouvoir mettre à jour
    l'annuaire entreprise périodiquement

    🏗️ comment: on stream {config.data_url} directement
    vers notre DB en utilisant zcat & psql
    """


def clone_table_create_wrapper(ti) -> None:

    config: CloneConfig = xcom_pull(ti, XCOMS.CONFIG)

    logger.info(task_info_get(config))
    log.preview("Configuration", config.model_dump())

    clone_ae_table_create(
        data_url=config.data_url,
        file_downloaded=config.file_downloaded,
        file_unpacked=config.file_unpacked,
        table_name=config.table_name,
        table_schema_file_path=config.table_schema_file_path,
        run_timestamp=config.run_timestamp,
        dry_run=config.dry_run,
    )


def clone_table_create_task(dag: DAG) -> PythonOperator:
    return PythonOperator(
        task_id=TASKS.TABLE_CREATE,
        python_callable=clone_table_create_wrapper,
        dag=dag,
    )
