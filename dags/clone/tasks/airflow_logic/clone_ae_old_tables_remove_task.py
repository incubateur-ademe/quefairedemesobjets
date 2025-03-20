"""Performs crawl checks on the URLs"""

import logging

from airflow import DAG
from airflow.operators.python import PythonOperator
from clone.config import (
    SCHEMAS_PREFIX,
    TABLES,
    TASKS,
    VIEW_IN_USE_SUFFIX,
    XCOMS,
    xcom_pull,
)
from clone.tasks.business_logic.clone_old_tables_remove import (
    clone_ae_old_tables_remove,
)

logger = logging.getLogger(__name__)


def task_info_get():
    return f"""
    ============================================================
    Description de la tâche "{TASKS.TABLES_OLD_REMOVE}"
    ============================================================
    💡 quoi: suppression des anciennes tables

    🎯 pourquoi: on en a plus besoin, on libère la DB

    🏗️ comment: dynamiquement on essaye de trouver les
    tables qui on le préfixe {SCHEMAS_PREFIX} mais qui ne sont
    ni les nouvelles tables ni les vues utilisées
    """


def clone_ea_old_tables_remove_wrapper(ti, params) -> None:
    logger.info(task_info_get())

    table_names = xcom_pull(ti, XCOMS.TABLE_NAMES)
    clone_ae_old_tables_remove(
        keep_table_names=list(table_names.values()),
        keep_view_names=[
            f"{SCHEMAS_PREFIX}_{TABLES.EA_UNITE.kind}_{VIEW_IN_USE_SUFFIX}",
            f"{SCHEMAS_PREFIX}_{TABLES.EA_ETAB.kind}_{VIEW_IN_USE_SUFFIX}",
        ],
        table_prefix=SCHEMAS_PREFIX,
        dry_run=params.get("dry_run", True),
    )


def clone_ea_old_tables_remove_task(dag: DAG) -> PythonOperator:
    return PythonOperator(
        task_id=TASKS.TABLES_OLD_REMOVE,
        python_callable=clone_ea_old_tables_remove_wrapper,
        dag=dag,
    )
