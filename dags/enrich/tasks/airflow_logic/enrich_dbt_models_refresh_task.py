"""Refresh DBT models for enrichment DAGs"""

import logging

from airflow import DAG
from airflow.exceptions import AirflowSkipException
from airflow.operators.bash import BashOperator
from airflow.operators.python import PythonOperator
from enrich.config import TASKS, XCOMS, xcom_pull

logger = logging.getLogger(__name__)


def task_info_get(dbt_model_refresh_command: str):
    return f"""
    ============================================================
    Description de la tâche "{TASKS.ENRICH_DBT_MODELS_REFRESH}"
    ============================================================
    💡 quoi: rafraichissement des modèles DBT

    🎯 pourquoi: avoir des suggestions fraiches

    🏗️ comment: via commande: {dbt_model_refresh_command}
    """


def enrich_dbt_models_refresh_wrapper(ti) -> None:

    # Config
    config = xcom_pull(ti, XCOMS.CONFIG)

    logger.info(task_info_get(config.dbt_models_refresh_command))
    logger.info(f"📖 Configuration:\n{config.model_dump_json(indent=2)}")

    if not config.dbt_models_refresh:
        raise AirflowSkipException("🚫 Rafraîchissement des modèles DBT désactivé")

    logger.info(
        f"🔄 Rafraîchissement des modèles DBT: {config.dbt_models_refresh_command}"
    )
    bash = BashOperator(
        task_id=TASKS.ENRICH_DBT_MODELS_REFRESH + "_bash",
        bash_command=config.dbt_build_command,
    )
    bash.execute(context=ti.get_template_context())


def enrich_dbt_models_refresh_task(
    dag: DAG,
) -> PythonOperator:
    return PythonOperator(
        task_id=TASKS.ENRICH_DBT_MODELS_REFRESH,
        python_callable=enrich_dbt_models_refresh_wrapper,
        dag=dag,
    )
