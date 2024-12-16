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
    df_propositionservice = kwargs["ti"].xcom_pull(task_ids="load_propositionservice")
    df_revisionpropositionservice = kwargs["ti"].xcom_pull(
        task_ids="load_revisionpropositionservice"
    )
    df_propositionservice_sous_categories = kwargs["ti"].xcom_pull(
        task_ids="load_propositionservice_sous_categories"
    )
    df_revisionpropositionservice_sous_categories = kwargs["ti"].xcom_pull(
        task_ids="load_revisionpropositionservice_sous_categories"
    )
    df_revisionacteur = kwargs["ti"].xcom_pull(task_ids="load_revisionacteur")

    log.preview("df_propositionservice", df_propositionservice)
    log.preview("df_revisionpropositionservice", df_revisionpropositionservice)
    log.preview(
        "df_propositionservice_sous_categories", df_propositionservice_sous_categories
    )
    log.preview(
        "df_revisionpropositionservice_sous_categories",
        df_revisionpropositionservice_sous_categories,
    )
    log.preview("df_revisionacteur", df_revisionacteur)

    return compute_ps(
        df_propositionservice=df_propositionservice,
        df_revisionpropositionservice=df_revisionpropositionservice,
        df_propositionservice_sous_categories=df_propositionservice_sous_categories,
        df_revisionpropositionservice_sous_categories=df_revisionpropositionservice_sous_categories,
        df_revisionacteur=df_revisionacteur,
    )
