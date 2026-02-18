import logging

from acteurs.tasks.business_logic.copy_displayed_data_from_warehouse_task import (
    copy_displayed_data_from_warehouse,
)
from airflow.operators.python import PythonOperator

logger = logging.getLogger(__name__)


def copy_displayed_data_from_warehouse_task():
    return PythonOperator(
        task_id="copy_displayed_data_from_warehouse",
        python_callable=copy_displayed_data_from_warehouse_wrapper,
    )


def copy_displayed_data_from_warehouse_wrapper(ti, params):
    copy_displayed_data_from_warehouse()
