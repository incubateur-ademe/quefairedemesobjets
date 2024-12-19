import logging

from airflow import DAG
from airflow.operators.python import PythonOperator
from sources.tasks.business_logic.serialize_to_json import db_data_prepare
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
    df_ps = kwargs["ti"].xcom_pull(task_ids="propose_ps")["df"]
    df_ps_sscat = kwargs["ti"].xcom_pull(task_ids="propose_ps_sscat")
    df_labels = kwargs["ti"].xcom_pull(task_ids="propose_labels")
    df_acteur_services = kwargs["ti"].xcom_pull(task_ids="propose_acteur_services")

    log.preview("df_acteur_to_delete", df_acteur_to_delete)
    log.preview("df_actors", df_actors)
    log.preview("df_ps", df_ps)
    log.preview("df_ps_sscat", df_ps_sscat)
    log.preview("df_labels", df_labels)
    log.preview("df_acteur_services", df_acteur_services)

    return db_data_prepare(
        df_acteur_to_delete=df_acteur_to_delete,
        df_actors=df_actors,
        df_ps=df_ps,
        df_ps_sscat=df_ps_sscat,
        df_labels=df_labels,
        df_acteur_services=df_acteur_services,
    )
