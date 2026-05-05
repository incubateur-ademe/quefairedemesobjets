"""Performs crawl checks on the URLs"""

import logging

from airflow import DAG
from airflow.providers.standard.operators.python import PythonOperator
from clone.config.models import CloneConfig
from clone.config.tasks import TASKS
from clone.config.xcoms import XCOMS, xcom_pull
from clone.tasks.business_logic.clone_old_tables_remove import clone_old_tables_remove
from utils import logging_utils as log

logger = logging.getLogger(__name__)


def task_info_get(config: CloneConfig) -> str:
    return f"""
    ============================================================
    Description de la tâche "{TASKS.OLD_TABLES_REMOVE}"
    ============================================================
    💡 quoi: suppression des anciennes tables

    🎯 pourquoi: on en a plus besoin, on libère la DB

    🏗️ comment: dynamiquement on essaye de trouver les
    tables au motif {config.table_name_pattern} mais
    qui qui ne sont pas {config.table_name}
    """


def clone_old_tables_remove_wrapper(ti) -> None:

    config: CloneConfig = xcom_pull(ti, XCOMS.CONFIG)

    logger.info(task_info_get(config))
    log.preview("Configuration", config.model_dump())

    clone_old_tables_remove(
        keep_table_name=config.table_name,
        remove_table_name_pattern=config.table_name_pattern,
        dry_run=config.dry_run,
    )


def clone_old_tables_remove_task(dag: DAG) -> PythonOperator:
    return PythonOperator(
        task_id=TASKS.OLD_TABLES_REMOVE,
        python_callable=clone_old_tables_remove_wrapper,
        dag=dag,
    )
