"""Performs crawl checks on the URLs"""

import logging

from airflow import DAG
from airflow.exceptions import AirflowSkipException
from airflow.operators.bash import BashOperator
from airflow.operators.python import PythonOperator
from clone.config import (
    TASKS,
    XCOMS,
    CloneConfig,
    xcom_pull,
)
from utils import logging_utils as log

logger = logging.getLogger(__name__)


def task_info_get(config: CloneConfig) -> str:
    return f"""
    ============================================================
    Description de la tâche "{TASKS.DBT_BUILD}"
    ============================================================
    💡 quoi: build dbt

    🎯 pourquoi: rafraichir les modèles DBT après import des données

    🏗️ comment: exécuter commande '{config.dbt_build_command}' si
    dbt_build_skip=False (actuellement={config.dbt_build_skip})
    """


def clone_dbt_build_wrapper(ti) -> None:

    config: CloneConfig = xcom_pull(ti, XCOMS.CONFIG)
    logger.info(task_info_get(config))
    log.preview("Configuration", config.model_dump())
    logger.info(f"Commande DBT: {config.dbt_build_command}")

    if config.dry_run:
        raise AirflowSkipException("✋ dry_run=True, on s'arrête là")
    if config.dbt_build_skip:
        raise AirflowSkipException("✋ dbt_build_skip=True, on s'arrête là")

    bash = BashOperator(
        task_id=TASKS.DBT_BUILD + "_bash",
        bash_command=config.dbt_build_command,
    )
    bash.execute(context=ti.get_template_context())


def clone_dbt_build_task(dag: DAG) -> PythonOperator:
    return PythonOperator(
        task_id=TASKS.DBT_BUILD,
        python_callable=clone_dbt_build_wrapper,
        dag=dag,
    )
