"""Performs crawl checks on the URLs"""

import logging

from airflow import DAG
from airflow.operators.python import PythonOperator
from clone.config import (
    TABLES,
    TASKS,
    VIEW_NAME_ETAB,
    VIEW_NAME_UNITE,
    XCOMS,
    xcom_pull,
)
from clone.tasks.business_logic.clone_ae_views_in_use_switch import (
    clone_ae_views_in_use_switch,
)

logger = logging.getLogger(__name__)


def task_info_get():
    return f"""
    ============================================================
    Description de la tâche "{TASKS.VIEWS_SWITCH}"
    ============================================================
    💡 quoi: Changement des vues {VIEW_NAME_ETAB} et {VIEW_NAME_UNITE}

    🎯 pourquoi: rendre les nouvelles tables actives

    🏗️ comment: on recréer le SQL des vues en les faisant
    pointer vers les nouvelles tables
    """


def clone_ea_views_in_use_switch_wrapper(ti, params) -> None:
    logger.info(task_info_get())

    table_names = xcom_pull(ti, XCOMS.TABLE_NAMES)
    clone_ae_views_in_use_switch(
        table_name_unite=table_names[TABLES.UNITE.kind],
        table_name_etab=table_names[TABLES.ETAB.kind],
        view_name_unite=VIEW_NAME_UNITE,
        view_name_etab=VIEW_NAME_ETAB,
        dry_run=params.get("dry_run", True),
    )


def clone_ea_views_in_use_switch_task(dag: DAG) -> PythonOperator:
    return PythonOperator(
        task_id=TASKS.VIEWS_SWITCH,
        python_callable=clone_ea_views_in_use_switch_wrapper,
        dag=dag,
    )
