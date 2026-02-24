"""Performs crawl checks on the URLs"""

import logging

from airflow import DAG
from airflow.providers.standard.operators.python import PythonOperator
from clone.config import TASKS, XCOMS, CloneConfig, xcom_pull
from clone.tasks.business_logic.clone_view_in_use_switch import clone_view_in_use_switch
from utils import logging_utils as log

logger = logging.getLogger(__name__)


def task_info_get(config: CloneConfig) -> str:
    return f"""
    ============================================================
    Description de la tâche "{TASKS.VIEW_IN_USE_SWITCH}"
    ============================================================
    💡 quoi: Changement de la vue {config.view_name}

    🎯 pourquoi: rendre le nouvelle table active

    🏗️ comment: on recréer la vue en la faisant pointé
    vers {config.table_name}
    """


def clone_view_in_use_switch_wrapper(ti) -> None:

    config: CloneConfig = xcom_pull(ti, XCOMS.CONFIG)

    logger.info(task_info_get(config))
    log.preview("Configuration", config.model_dump())

    clone_view_in_use_switch(
        view_schema_file_path=config.view_schema_file_path,
        view_name=config.view_name,
        table_name=config.table_name,
        dry_run=config.dry_run,
    )


def clone_view_in_use_switch_task(dag: DAG) -> PythonOperator:
    return PythonOperator(
        task_id=TASKS.VIEW_IN_USE_SWITCH,
        python_callable=clone_view_in_use_switch_wrapper,
        dag=dag,
    )
