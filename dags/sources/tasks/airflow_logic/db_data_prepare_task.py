import logging

from airflow import DAG
from airflow.operators.python import PythonOperator
from sources.tasks.business_logic.db_data_prepare import db_data_prepare
from sources.tasks.business_logic.read_mapping_from_postgres import (
    read_mapping_from_postgres,
)
from utils import logging_utils as log

logger = logging.getLogger(__name__)


def db_data_prepare_task(dag: DAG) -> PythonOperator:
    return PythonOperator(
        task_id="db_data_prepare",
        python_callable=db_data_prepare_wrapper,
        dag=dag,
    )


def db_data_prepare_wrapper(**kwargs):
    df_acteur_to_delete = kwargs["ti"].xcom_pull(task_ids="propose_acteur_to_delete")[
        "df_acteur_to_delete"
    ]
    df_actors = kwargs["ti"].xcom_pull(task_ids="propose_acteur_changes")["df"]
    df_ps = kwargs["ti"].xcom_pull(task_ids="propose_services")["df"]
    df_pssc = kwargs["ti"].xcom_pull(task_ids="propose_services_sous_categories")
    df_labels = kwargs["ti"].xcom_pull(task_ids="propose_labels")
    df_acteur_services = kwargs["ti"].xcom_pull(task_ids="propose_acteur_services")
    df_acteurs_from_db = kwargs["ti"].xcom_pull(task_ids="db_read_acteur")
    source_id_by_code = read_mapping_from_postgres(table_name="qfdmo_source")
    acteurtype_id_by_code = read_mapping_from_postgres(table_name="qfdmo_acteurtype")

    log.preview("df_acteur_to_delete", df_acteur_to_delete)
    log.preview("df_actors", df_actors)
    log.preview("df_ps", df_ps)
    log.preview("df_pssc", df_pssc)
    log.preview("df_labels", df_labels)
    log.preview("df_acteur_services", df_acteur_services)
    log.preview("df_acteurs_from_db", df_acteurs_from_db)
    log.preview("source_id_by_code", source_id_by_code)
    log.preview("acteurtype_id_by_code", acteurtype_id_by_code)

    return db_data_prepare(
        df_acteur_to_delete=df_acteur_to_delete,
        df_acteur=df_actors,
        df_ps=df_ps,
        df_pssc=df_pssc,
        df_labels=df_labels,
        df_acteur_services=df_acteur_services,
        df_acteurs_from_db=df_acteurs_from_db,
        source_id_by_code=source_id_by_code,
        acteurtype_id_by_code=acteurtype_id_by_code,
    )
