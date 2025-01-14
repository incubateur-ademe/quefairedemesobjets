from airflow.models import DAG
from airflow.operators.python import PythonOperator
from suggestions.business_logic.db_write_validsuggestions import (
    db_write_validsuggestions,
)
from utils import logging_utils as log


def db_write_validsuggestions_task(dag: DAG) -> PythonOperator:
    return PythonOperator(
        task_id="db_write_validsuggestions",
        python_callable=db_write_validsuggestions_wrapper,
        dag=dag,
    )


def db_write_validsuggestions_wrapper(**kwargs):
    data_from_db = kwargs["ti"].xcom_pull(task_ids="db_normalize_suggestion")

    log.preview("data_from_db acteur", data_from_db["actors"])
    log.preview("data_from_db change_type", data_from_db["change_type"])

    return db_write_validsuggestions(data_from_db=data_from_db)
