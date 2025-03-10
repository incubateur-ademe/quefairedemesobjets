"""Performs crawl checks on the URLs"""

import logging

from airflow import DAG
from airflow.operators.python import PythonOperator
from clone.config import TABLES, TASKS, XCOMS, xcom_pull
from clone.tasks.business_logic.clone_ae_table_create import clone_ae_table_create

logger = logging.getLogger(__name__)


def task_info_get():
    return f"""
    ============================================================
    Description de la tâche "{TASKS.TABLE_CREATE_UNITE}"
    ============================================================
    💡 quoi: créer la table {TABLES.UNITE.kind} à partir
    de {TABLES.UNITE.url}

    🎯 pourquoi: c'est le but de ce DAG, pouvoir mettre à jour
    l'annuaire entreprise périodiquement

    🏗️ comment: on stream {TABLES.UNITE.url} directement
    vers notre DB en utilisant zcat & psql
    """


def clone_ea_table_create_unite_wrapper(ti, params) -> None:
    logger.info(task_info_get())

    table_names = xcom_pull(ti, XCOMS.TABLE_NAMES)
    table_name = table_names[TABLES.UNITE.kind]
    clone_ae_table_create(
        csv_url=TABLES.UNITE.url,
        table_kind=TABLES.UNITE.kind,
        table_name=table_name,
        dry_run=params.get("dry_run", True),
    )


def clone_ea_table_create_unite_task(dag: DAG) -> PythonOperator:
    return PythonOperator(
        task_id=TASKS.TABLE_CREATE_UNITE,
        python_callable=clone_ea_table_create_unite_wrapper,
        dag=dag,
    )
