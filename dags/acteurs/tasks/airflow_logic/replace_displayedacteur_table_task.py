"""Performs crawl checks on the URLs"""

import logging

from acteurs.tasks.business_logic.replace_displayedacteur_table import (
    replace_displayedacteur_table,
)
from airflow import DAG
from airflow.operators.python import PythonOperator

logger = logging.getLogger(__name__)

TASK_NAME = "replace_displayedacteur_table"


def task_info_get():
    return f"""
    ============================================================
    Description de la tâche "{TASK_NAME}"
    ============================================================
    💡 quoi: Remplace les tables liée au modèle DisplayedActeur par celles calculées
    par DBT

    🎯 pourquoi: Mise à jour des données publié par la carte

    🏗️ comment: Renommer les tables préfixées par `exposure_carte_` et supprimer les
    anciennes préfixées par `qfdmo_displayed`
    """


def replace_displayedacteur_table_wrapper(ti, params) -> None:
    logger.info(task_info_get())

    replace_displayedacteur_table()


def replace_displayedacteur_table_task(dag: DAG) -> PythonOperator:
    return PythonOperator(
        task_id=TASK_NAME,
        python_callable=replace_displayedacteur_table_wrapper,
        dag=dag,
    )
