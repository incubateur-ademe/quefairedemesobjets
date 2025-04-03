"""Performs crawl checks on the URLs"""

import logging

from airflow import DAG
from airflow.operators.python import PythonOperator
from clone.config import TASKS, XCOMS, CloneConfig
from clone.tasks.business_logic.clone_config_create import clone_config_create
from utils import logging_utils as log

logger = logging.getLogger(__name__)


def task_info_get():
    return f"""
    ============================================================
    Description de la tâche "{TASKS.CONFIG_CREATE}"
    ============================================================
    💡 quoi: création de la config du DAG

    🎯 pourquoi: réutilisation à travers tout le DAG

    🏗️ comment: modèle pydantic qui valide et génère une config
    """


def clone_config_create_wrapper(ti, params) -> None:

    config: CloneConfig = clone_config_create(params)

    logger.info(task_info_get())
    log.preview("Configuration générée", config.model_dump())

    ti.xcom_push(key=XCOMS.CONFIG, value=config)


def clone_config_create_task(dag: DAG) -> PythonOperator:
    return PythonOperator(
        task_id=TASKS.CONFIG_CREATE,
        python_callable=clone_config_create_wrapper,
        dag=dag,
    )
