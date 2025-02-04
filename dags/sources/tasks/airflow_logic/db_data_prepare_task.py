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
    df_acteur = kwargs["ti"].xcom_pull(task_ids="compute_link_tables")
    df_acteur_from_db = kwargs["ti"].xcom_pull(task_ids="keep_acteur_changed")[
        "df_acteur_from_db"
    ]

    log.preview("df_acteur", df_acteur)
    log.preview("df_acteur_from_db", df_acteur_from_db)

    return db_data_prepare(
        df_acteur=df_acteur,
        df_acteur_from_db=df_acteur_from_db,
    )
