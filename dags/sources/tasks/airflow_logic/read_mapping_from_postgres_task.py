import logging
from datetime import timedelta

from airflow import DAG
from airflow.operators.python import PythonOperator
from sources.tasks.business_logic.read_mapping_from_postgres import (
    read_mapping_from_postgres,
)
from utils import logging_utils as log

logger = logging.getLogger(__name__)


def read_mapping_from_postgres_task(
    *,
    dag: DAG,
    table_name: str,
    task_id: str,
    retries: int = 0,
    retry_delay: timedelta = timedelta(minutes=2),
) -> PythonOperator:

    return PythonOperator(
        task_id=task_id,
        python_callable=read_mapping_from_postgres_wrapper,
        op_kwargs={"table_name": table_name},
        dag=dag,
        retries=retries,
        retry_delay=retry_delay,
    )


def read_mapping_from_postgres_wrapper(**kwargs):
    table_name = kwargs["table_name"]

    log.preview("table_name", table_name)

    return read_mapping_from_postgres(table_name=table_name)
