import logging

from acteurs.tasks.business_logic.copy_db_schema import copy_db_schema
from airflow.providers.standard.operators.python import PythonOperator

logger = logging.getLogger(__name__)


def copy_db_schema_task():
    return PythonOperator(
        task_id="copy_db_schema",
        python_callable=copy_db_schema_wrapper,
    )


def copy_db_schema_wrapper(ti, params):
    copy_db_schema()
