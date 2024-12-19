import logging

from airflow import DAG
from airflow.operators.python import PythonOperator
from compute_acteurs.tasks.business_logic import db_data_write
from utils import logging_utils as log

logger = logging.getLogger(__name__)


def db_data_write_task(dag: DAG) -> PythonOperator:
    return PythonOperator(
        task_id="write_data_to_postgres",
        python_callable=db_data_write_wrapper,
        dag=dag,
    )


def db_data_write_wrapper(**kwargs):
    df_acteur_merged = kwargs["ti"].xcom_pull(task_ids="apply_corrections_acteur")[
        "df_acteur_merged"
    ]
    df_labels_updated = kwargs["ti"].xcom_pull(task_ids="deduplicate_labels")
    df_acteur_services_updated = kwargs["ti"].xcom_pull(
        task_ids="deduplicate_acteur_serivces"
    )
    df_acteur_sources_updated = kwargs["ti"].xcom_pull(
        task_ids="deduplicate_acteur_sources"
    )
    task_output = kwargs["ti"].xcom_pull(task_ids="deduplicate_ps")
    df_ps_merged = task_output["df_final_ps_updated"]
    df_ps_sscat_merged = task_output["df_final_sscat"]

    log.preview("df_acteur_merged", df_acteur_merged)
    log.preview("df_labels_updated", df_labels_updated)
    log.preview("df_acteur_services_updated", df_acteur_services_updated)
    log.preview("df_acteur_sources_updated", df_acteur_sources_updated)
    log.preview("df_ps_merged", df_ps_merged)
    log.preview(
        "df_ps_sscat_merged",
        df_ps_sscat_merged,
    )

    return db_data_write(
        df_acteur_merged=df_acteur_merged,
        df_labels_updated=df_labels_updated,
        df_acteur_services_updated=df_acteur_services_updated,
        df_acteur_sources_updated=df_acteur_sources_updated,
        df_ps_merged=df_ps_merged,
        df_ps_sscat_merged=df_ps_sscat_merged,
    )
