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
    Description de la tâche "{TASKS.TABLE_CREATE_ETAB}"
    ============================================================
    💡 quoi: créer la table {TABLES.ETAB.kind} à partir
    de {TABLES.ETAB.csv_url}

    🎯 pourquoi: c'est le but de ce DAG, pouvoir mettre à jour
    l'annuaire entreprise périodiquement

    🏗️ comment: on stream {TABLES.ETAB.csv_url} directement
    vers notre DB en utilisant zcat & psql
    """


def clone_ea_table_create_etab_wrapper(ti, params) -> None:
    logger.info(task_info_get())

    table_names = xcom_pull(ti, XCOMS.TABLE_NAMES)
    table_name = table_names[TABLES.ETAB.kind]
    clone_ae_table_create(
        csv_url=TABLES.ETAB.csv_url,
        csv_filestem=TABLES.ETAB.csv_filestem,
        table_kind=TABLES.ETAB.kind,
        table_name=table_name,
        dry_run=params.get("dry_run", True),
    )


def clone_ea_table_create_etab_task(dag: DAG) -> PythonOperator:
    return PythonOperator(
        task_id=TASKS.TABLE_CREATE_ETAB,
        python_callable=clone_ea_table_create_etab_wrapper,
        dag=dag,
    )
