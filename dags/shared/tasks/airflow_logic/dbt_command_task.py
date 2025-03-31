"""Reusable task to run a dbt command in a DAG
(ex: after clone DAGs -> rebuild the corresponding DBT models).

TODO: to reuse multiple times in 1 DAG, add a prefix to make task_id unique"""

import logging

from airflow import DAG
from airflow.operators.bash import BashOperator

logger = logging.getLogger(__name__)


def dbt_command_task(dag: DAG) -> BashOperator:
    params = dag.params
    dbt_command = params.get("dbt_command", "").strip()

    logger.info("Commande DBT à exécuter: %s", dbt_command)

    if not dbt_command:
        raise ValueError("Paramètre dbt_command requis")

    if params.get("dry_run") is True:
        logger.info("Mode dry_run activé, commande DBT non exécutée")
        dbt_command = ""

    return BashOperator(
        task_id="dbt_command",
        bash_command=dbt_command,
        dag=dag,
    )
