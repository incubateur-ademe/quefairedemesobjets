import os

from airflow.providers.standard.operators.python import ShortCircuitOperator


def check_is_prod_env() -> bool:
    """Check if we are in a production environment."""
    return os.environ.get("ENVIRONMENT") == "prod"


def check_is_prod_env_task():
    """
    Return a ShortCircuitOperator that runs all following tasks
    if we are in a production environment.
    """
    return ShortCircuitOperator(
        task_id="check_is_prod_env",
        python_callable=check_is_prod_env,
    )
