import logging

from acteurs.tasks.business_logic.copy_db_data import copy_db_data
from airflow.operators.python import PythonOperator

logger = logging.getLogger(__name__)


def copy_db_data_task():
    return PythonOperator(
        task_id="copy_db_data",
        python_callable=copy_db_data_wrapper,
    )


def copy_db_data_wrapper(ti, params):
    copy_db_data()
