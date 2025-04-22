"""Reusable task to run a dbt command in a DAG"""

import logging

from airflow import DAG
from airflow.operators.bash import BashOperator

logger = logging.getLogger(__name__)


def dbt_command_task(dag: DAG, task_id: str) -> BashOperator:
    params = dag.params
    dbt_command = params.get("dbt_command", "").strip()

    logger.info("Commande DBT à exécuter: %s", dbt_command)

    if not dbt_command:
        raise ValueError("Paramètre dbt_command requis")
    if not dbt_command.startswith("dbt "):
        raise ValueError("La commande DBT doit commencer par 'dbt '")

    if params.get("dry_run") is True:
        logger.info("Mode dry_run activé, commande DBT non exécutée")
        dbt_command = "echo 'dry_run: commande DBT non exécutée'"

    return BashOperator(
        task_id=task_id,
        bash_command=dbt_command,
        dag=dag,
    )
