"""Performs crawl checks on the URLs"""

import logging

from acteurs.tasks.business_logic.replace_acteur_table import replace_acteur_table
from airflow import DAG
from airflow.operators.python import PythonOperator

from utils import logging_utils as log

logger = logging.getLogger(__name__)

TASK_NAME = "replace_acteur_table"


def task_info_get(prefix_django: str, prefix_dbt: str):
    return f"""
    ============================================================
    Description de la tâche "{TASK_NAME}"
    ============================================================
    💡 quoi: Remplace les tables des modèles django par celles calculées par DBT

    🎯 pourquoi: Mise à jour des données publiées par la carte

    🏗️ comment:
    - Renommer les tables préfixées par `{prefix_django}` en vue de leur suppression
    - Renommer les tables préfixées par `{prefix_dbt}` en les renommant avec le préfixe
      `{prefix_django}`
    - Supprimer les tables qui ont été renommées précédemment
    """


def replace_acteur_table_wrapper(
    ti,
    params,
    *,
    prefix_django: str,
    prefix_dbt: str,
) -> None:
    logger.info(task_info_get(prefix_django, prefix_dbt))

    log.preview("Préfixe des tables du modèle Django", prefix_django)
    log.preview("Préfixe des tables calculées par DBT", prefix_dbt)
    replace_acteur_table(
        prefix_django=prefix_django,
        prefix_dbt=prefix_dbt,
    )


def replace_acteur_table_task(
    dag: DAG,
    prefix_django: str,
    prefix_dbt: str,
) -> PythonOperator:
    task_name = f"replace_{prefix_django}_by_{prefix_dbt}_table"
    return PythonOperator(
        task_id=task_name,
        python_callable=replace_acteur_table_wrapper,
        dag=dag,
        op_kwargs={
            "prefix_django": prefix_django,
            "prefix_dbt": prefix_dbt,
        },
    )
