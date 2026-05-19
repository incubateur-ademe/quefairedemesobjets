"""Performs crawl checks on the URLs"""

import logging

from airflow import DAG
from airflow.providers.standard.operators.python import PythonOperator
from clone.config.models import CloneConfig
from clone.config.tasks import TASKS
from clone.config.xcoms import XCOMS, xcom_push
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

    xcom_push(ti, XCOMS.CONFIG, config)


def clone_config_create_task(dag: DAG) -> PythonOperator:
    return PythonOperator(
        task_id=TASKS.CONFIG_CREATE,
        python_callable=clone_config_create_wrapper,
        dag=dag,
    )
