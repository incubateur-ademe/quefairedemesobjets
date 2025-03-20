"""Performs crawl checks on the URLs"""

import logging

from airflow import DAG
from airflow.operators.python import PythonOperator
from clone.config import DIR_SQL_VALIDATIONS, TABLES, TASKS, XCOMS, xcom_pull
from clone.tasks.business_logic.clone_table_validate import clone_ae_table_validate

logger = logging.getLogger(__name__)


def task_info_get():
    return f"""
    ============================================================
    Description de la tâche "{TASKS.TABLE_VALIDATE_UNITE}"
    ============================================================
    💡 quoi: valider la table {TABLES.EA_UNITE.kind}

    🎯 pourquoi: c'est le but de ce DAG, pouvoir mettre à jour
    l'annuaire entreprise périodiquement

    🏗️ comment: en rejouant les requêtes présentes dans
    {DIR_SQL_VALIDATIONS / TABLES.EA_UNITE.kind} sur la table
    créée précédemment
    """


def clone_ea_table_validate_unite_wrapper(ti, params) -> None:
    logger.info(task_info_get())

    table_names = xcom_pull(ti, XCOMS.TABLE_NAMES)
    table_name = table_names[TABLES.EA_UNITE.kind]
    clone_ae_table_validate(
        table_kind=TABLES.EA_UNITE.kind,
        table_name=table_name,
        dry_run=params.get("dry_run", True),
    )


def clone_ea_table_validate_unite_task(dag: DAG) -> PythonOperator:
    return PythonOperator(
        task_id=TASKS.TABLE_VALIDATE_UNITE,
        python_callable=clone_ea_table_validate_unite_wrapper,
        dag=dag,
    )
