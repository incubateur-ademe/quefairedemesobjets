import os

from airflow.operators.python import ShortCircuitOperator


def check_isnt_prod_env() -> bool:
    """Check if we are not in a production environment."""
    return os.environ.get("ENVIRONMENT") != "prod"


def check_isnt_prod_env_task():
    """
    Return a ShortCircuitOperator that skips all following tasks
    if we are not in a production environment.
    """
    return ShortCircuitOperator(
        task_id="check_isnt_prod_env",
        python_callable=check_isnt_prod_env,
    )
