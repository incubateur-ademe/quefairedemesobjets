"""Run or test a DBT normalization after a clone.

Mutualized across clone DAGs: the full DBT commands (run + test) are exposed as
editable Airflow params via ``clone_dbt_params(...)``. A DAG that adds these
params gets the DBT tasks inserted automatically by ``chain_tasks`` (which
detects them in ``dag.params``). DAGs without them keep their chain unchanged.
"""

import logging
from dataclasses import dataclass

from airflow import DAG
from airflow.providers.standard.operators.bash import BashOperator
from airflow.providers.standard.operators.python import PythonOperator
from airflow.sdk import Param
from airflow.sdk.exceptions import AirflowSkipException
from clone.config.tasks import TASKS
from shared.config.dbt_commands import DBT_RUN, DBT_TEST

logger = logging.getLogger(__name__)

# Param keys exposed in the Airflow UI for DAGs that normalize via DBT.
PARAM_RUN_DBT = "run_dbt"
PARAM_DBT_RUN_COMMAND = "dbt_run_command"
PARAM_DBT_TEST_COMMAND = "dbt_test_command"


def clone_dbt_params(dbt_select: str) -> dict[str, Param]:
    """Build the DBT params for a clone DAG from a DBT selector.

    The full commands (``dbt run --select ...`` / ``dbt test --select ...``) are
    exposed as editable string params, so they can be overridden at runtime.
    """
    return {
        PARAM_RUN_DBT: Param(
            True,
            type="boolean",
            description_md=(
                "🔄 Si coché, exécute la normalisation DBT (run + test)"
                " après le clone.\n🔴 Désactiver uniquement pour des tests."
            ),
        ),
        PARAM_DBT_RUN_COMMAND: Param(
            f"{DBT_RUN} {dbt_select}",
            type="string",
            description_md="🔄 Commande DBT exécutée pour normaliser les données",
        ),
        PARAM_DBT_TEST_COMMAND: Param(
            f"{DBT_TEST} {dbt_select}",
            type="string",
            description_md="🧪 Commande DBT exécutée pour tester la normalisation",
        ),
    }


@dataclass(frozen=True)
class CloneDbtAction:
    task_id: str
    command_param: str
    what: str
    why: str
    log_emoji: str
    log_label: str


RUN_ACTION = CloneDbtAction(
    task_id=TASKS.DBT_RUN,
    command_param=PARAM_DBT_RUN_COMMAND,
    what="normalisation des données clonées via DBT",
    why="exposer des données propres en aval du clone",
    log_emoji="🔄",
    log_label="Normalisation",
)

TEST_ACTION = CloneDbtAction(
    task_id=TASKS.DBT_TEST,
    command_param=PARAM_DBT_TEST_COMMAND,
    what="exécution des tests DBT de normalisation",
    why="valider la normalisation avant de la considérer comme fraîche",
    log_emoji="🧪",
    log_label="Tests",
)


def task_info_get(action: CloneDbtAction, command: str) -> str:
    return f"""
    ============================================================
    Description de la tâche "{action.task_id}"
    ============================================================
    💡 quoi: {action.what}

    🎯 pourquoi: {action.why}

    🏗️ comment: via commande: {command}
    """


def clone_dbt_wrapper(action: CloneDbtAction, ti, params) -> None:
    command = params.get(action.command_param)
    if not command:
        raise AirflowSkipException(
            f"🚫 Aucune commande DBT configurée ({action.command_param})"
        )

    logger.info(task_info_get(action, command))

    if not params.get(PARAM_RUN_DBT, True):
        raise AirflowSkipException(
            f"🚫 Normalisation DBT désactivée ({PARAM_RUN_DBT}=False)"
        )

    if params.get("dry_run"):
        raise AirflowSkipException("🚱 dry_run: normalisation DBT non exécutée")

    logger.info(f"{action.log_emoji} {action.log_label} DBT: {command}")
    bash = BashOperator(
        task_id=action.task_id + "_bash",
        bash_command=command,
    )
    bash.execute(context=ti.get_template_context())


def clone_dbt_task(dag: DAG, action: CloneDbtAction) -> PythonOperator:
    return PythonOperator(
        task_id=action.task_id,
        python_callable=clone_dbt_wrapper,
        op_kwargs={"action": action},
        dag=dag,
    )


def clone_dbt_run_task(dag: DAG) -> PythonOperator:
    return clone_dbt_task(dag, RUN_ACTION)


def clone_dbt_test_task(dag: DAG) -> PythonOperator:
    return clone_dbt_task(dag, TEST_ACTION)
