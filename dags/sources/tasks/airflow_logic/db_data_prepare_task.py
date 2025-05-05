import logging

from airflow import DAG
from airflow.operators.python import PythonOperator
from sources.tasks.business_logic.db_data_prepare import db_data_prepare

from utils import logging_utils as log

logger = logging.getLogger(__name__)


def db_data_prepare_task(dag: DAG) -> PythonOperator:
    return PythonOperator(
        task_id="db_data_prepare",
        python_callable=db_data_prepare_wrapper,
        dag=dag,
    )


def db_data_prepare_wrapper(**kwargs):
    df_acteur_from_source = kwargs["ti"].xcom_pull(
        task_ids="keep_acteur_changed", key="df_acteur_from_source"
    )
    df_acteur_from_db = kwargs["ti"].xcom_pull(
        task_ids="keep_acteur_changed", key="df_acteur_from_db"
    )

    log.preview("df_acteur", df_acteur_from_source)
    log.preview("df_acteur_from_db", df_acteur_from_db)

    result = db_data_prepare(
        df_acteur=df_acteur_from_source,
        df_acteur_from_db=df_acteur_from_db,
    )

    kwargs["ti"].xcom_push(
        key="df_acteur_to_create", value=result["df_acteur_to_create"]
    )
    kwargs["ti"].xcom_push(
        key="df_acteur_to_update", value=result["df_acteur_to_update"]
    )
    kwargs["ti"].xcom_push(
        key="df_acteur_to_delete", value=result["df_acteur_to_delete"]
    )
    kwargs["ti"].xcom_push(key="metadata_to_update", value=result["metadata_to_update"])
    kwargs["ti"].xcom_push(key="metadata_to_create", value=result["metadata_to_create"])
    kwargs["ti"].xcom_push(key="metadata_to_delete", value=result["metadata_to_delete"])
