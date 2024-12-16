import logging

from airflow import DAG
from airflow.operators.python import PythonOperator
from compute_acteurs.tasks.business_logic import merge_labels
from utils import logging_utils as log

logger = logging.getLogger(__name__)


def merge_labels_task(dag: DAG) -> PythonOperator:
    return PythonOperator(
        task_id="merge_labels",
        python_callable=merge_labels_wrapper,
        dag=dag,
    )


def merge_labels_wrapper(**kwargs):
    df_acteur_labels = kwargs["ti"].xcom_pull(task_ids="load_acteur_labels")
    df_revisionacteur_labels = kwargs["ti"].xcom_pull(
        task_ids="load_revisionacteur_labels"
    )
    df_revisionacteur = kwargs["ti"].xcom_pull(task_ids="load_revisionacteur")

    log.preview("df_acteur_labels", df_acteur_labels)
    log.preview("df_revisionacteur_labels", df_revisionacteur_labels)
    log.preview("df_revisionacteur", df_revisionacteur)

    return merge_labels(
        df_acteur_labels=df_acteur_labels,
        df_revisionacteur_labels=df_revisionacteur_labels,
        df_revisionacteur=df_revisionacteur,
    )
