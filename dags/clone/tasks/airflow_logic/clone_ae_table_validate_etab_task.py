"""Performs crawl checks on the URLs"""

import logging

from airflow import DAG
from airflow.operators.python import PythonOperator
from clone.config import DIR_SQL_VALIDATIONS, TABLES, TASKS, XCOMS, xcom_pull
from clone.tasks.business_logic.clone_ae_table_validate import clone_ae_table_validate

logger = logging.getLogger(__name__)


def task_info_get():
    return f"""
    ============================================================
    Description de la tâche "{TASKS.TABLE_VALIDATE_ETAB}"
    ============================================================
    💡 quoi: valider la table {TABLES.ETAB.kind}

    🎯 pourquoi: c'est le but de ce DAG, pouvoir mettre à jour
    l'annuaire entreprise périodiquement

    🏗️ comment: en rejouant les requêtes présentes dans
    {DIR_SQL_VALIDATIONS / TABLES.ETAB.kind} sur la table
    créée précédemment
    """


def clone_ea_table_validate_etab_wrapper(ti, params) -> None:
    logger.info(task_info_get())

    table_names = xcom_pull(ti, XCOMS.TABLE_NAMES)
    table_name = table_names[TABLES.ETAB.kind]
    clone_ae_table_validate(
        table_kind=TABLES.ETAB.kind,
        table_name=table_name,
        dry_run=params.get("dry_run", True),
    )


def clone_ea_table_validate_etab_task(dag: DAG) -> PythonOperator:
    return PythonOperator(
        task_id=TASKS.TABLE_VALIDATE_ETAB,
        python_callable=clone_ea_table_validate_etab_wrapper,
        dag=dag,
    )
