"""Run or test DBT models for enrichment DAGs"""

import logging
from dataclasses import dataclass

from airflow import DAG
from airflow.providers.standard.operators.bash import BashOperator
from airflow.providers.standard.operators.python import PythonOperator
from airflow.sdk.exceptions import AirflowSkipException
from enrich.config.models import EnrichActeursClosedConfig
from enrich.config.tasks import TASKS

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class EnrichDbtModelsAction:
    task_id: str
    command_field: str
    what: str
    why: str
    log_emoji: str
    log_label: str


REFRESH_ACTION = EnrichDbtModelsAction(
    task_id=TASKS.ENRICH_DBT_MODELS_REFRESH,
    command_field="dbt_models_refresh_command",
    what="rafraichissement des modèles DBT",
    why="avoir des suggestions fraiches",
    log_emoji="🔄",
    log_label="Rafraîchissement",
)

TEST_ACTION = EnrichDbtModelsAction(
    task_id=TASKS.ENRICH_DBT_MODELS_TEST,
    command_field="dbt_models_test_command",
    what="exécution des tests DBT",
    why="valider les modèles avant les suggestions",
    log_emoji="🧪",
    log_label="Tests",
)


def task_info_get(action: EnrichDbtModelsAction, command: str) -> str:
    return f"""
    ============================================================
    Description de la tâche "{action.task_id}"
    ============================================================
    💡 quoi: {action.what}

    🎯 pourquoi: {action.why}

    🏗️ comment: via commande: {command}
    """


def enrich_dbt_models_wrapper(action: EnrichDbtModelsAction, ti, params) -> None:
    config = EnrichActeursClosedConfig(**params)
    command = getattr(config, action.command_field)
    logger.info(task_info_get(action, command))
    logger.info(f"📖 Configuration:\n{config.model_dump_json(indent=2)}")

    if not config.dbt_models_refresh:
        raise AirflowSkipException("🚫 Rafraîchissement des modèles DBT désactivé")

    logger.info(f"{action.log_emoji} {action.log_label} des modèles DBT: {command}")
    bash = BashOperator(
        task_id=action.task_id + "_bash",
        bash_command=command,
    )
    bash.execute(context=ti.get_template_context())


def enrich_dbt_models_task(dag: DAG, action: EnrichDbtModelsAction) -> PythonOperator:
    return PythonOperator(
        task_id=action.task_id,
        python_callable=enrich_dbt_models_wrapper,
        op_kwargs={"action": action},
        dag=dag,
    )


def enrich_dbt_models_refresh_task(dag: DAG) -> PythonOperator:
    return enrich_dbt_models_task(dag, REFRESH_ACTION)


def enrich_dbt_models_test_task(dag: DAG) -> PythonOperator:
    return enrich_dbt_models_task(dag, TEST_ACTION)
