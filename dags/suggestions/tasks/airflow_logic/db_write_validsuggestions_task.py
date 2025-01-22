from airflow.models import DAG
from airflow.operators.python import PythonOperator
from suggestions.tasks.business_logic.db_write_validsuggestions import (
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
    data_acteurs_normalized = kwargs["ti"].xcom_pull(task_ids="db_normalize_suggestion")

    log.preview("data_acteurs_normalized acteur", data_acteurs_normalized["acteur"])
    log.preview(
        "data_acteurs_normalized change_type", data_acteurs_normalized["change_type"]
    )

    return db_write_validsuggestions(data_acteurs_normalized=data_acteurs_normalized)
