import logging

from airflow import DAG
from airflow.operators.python import PythonOperator
from compute_acteurs.tasks.business_logic import compute_ps
from utils import logging_utils as log

logger = logging.getLogger(__name__)


def compute_ps_task(dag: DAG) -> PythonOperator:
    return PythonOperator(
        task_id="compute_ps",
        python_callable=compute_ps_wrapper,
        dag=dag,
    )


def compute_ps_wrapper(**kwargs):
    df_ps = kwargs["ti"].xcom_pull(task_ids="load_ps")
    df_rps = kwargs["ti"].xcom_pull(task_ids="load_rps")
    df_ps_sscat = kwargs["ti"].xcom_pull(task_ids="load_ps_sscat")
    df_rps_sscat = kwargs["ti"].xcom_pull(task_ids="load_rps_sscat")
    df_revisionacteur = kwargs["ti"].xcom_pull(task_ids="load_revisionacteur")

    log.preview("df_ps", df_ps)
    log.preview("df_rps", df_rps)
    log.preview("df_ps_sscat", df_ps_sscat)
    log.preview(
        "df_rps_sscat",
        df_rps_sscat,
    )
    log.preview("df_revisionacteur", df_revisionacteur)

    return compute_ps(
        df_ps=df_ps,
        df_rps=df_rps,
        df_ps_sscat=df_ps_sscat,
        df_rps_sscat=df_rps_sscat,
        df_revisionacteur=df_revisionacteur,
    )
