"""Performs crawl checks on the URLs"""

import logging

from airflow import DAG
from airflow.operators.python import PythonOperator
from clone.config import TASKS, XCOMS
from clone.tasks.business_logic.clone_table_name_prepare import (
    clone_ae_table_name_prepare,
)

logger = logging.getLogger(__name__)


def task_info_get():
    return f"""
    ============================================================
    Description de la tâche "{TASKS.TABLE_NAMES_PREP}"
    ============================================================
    💡 quoi: on génère le nom des tables SQL à venir

    🎯 pourquoi: car on s'en sert à plusieurs endroit (création
    des tables, switch de la vue) et donc on centralise la logique

    🏗️ comment: on ajoute un timestamp en suffixe des tables, le
    même timestamp étant utilisé pour un run donné
    """


def clone_ea_table_name_prepare_wrapper(ti, params) -> None:
    logger.info(task_info_get())

    table_names = clone_ae_table_name_prepare()
    ti.xcom_push(key=XCOMS.TABLE_NAMES, value=table_names)


def clone_ea_table_name_prepare_task(dag: DAG) -> PythonOperator:
    return PythonOperator(
        task_id=TASKS.TABLE_NAMES_PREP,
        python_callable=clone_ea_table_name_prepare_wrapper,
        dag=dag,
    )
