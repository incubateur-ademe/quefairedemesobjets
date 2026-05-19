"""Refresh DBT models for enrichment DAGs"""

import logging

from airflow import DAG
from airflow.providers.standard.operators.bash import BashOperator
from airflow.providers.standard.operators.python import PythonOperator
from airflow.sdk.exceptions import AirflowSkipException
from enrich.config.models import EnrichActeursClosedConfig
from enrich.config.tasks import TASKS

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


def enrich_dbt_models_refresh_wrapper(ti, params) -> None:

    # Config
    config = EnrichActeursClosedConfig(**params)
    logger.info(task_info_get(config.dbt_models_refresh_command))
    logger.info(f"📖 Configuration:\n{config.model_dump_json(indent=2)}")

    if not config.dbt_models_refresh:
        raise AirflowSkipException("🚫 Rafraîchissement des modèles DBT désactivé")

    logger.info(
        f"🔄 Rafraîchissement des modèles DBT: {config.dbt_models_refresh_command}"
    )
    bash = BashOperator(
        task_id=TASKS.ENRICH_DBT_MODELS_REFRESH + "_bash",
        bash_command=config.dbt_models_refresh_command,
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
