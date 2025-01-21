import logging

from airflow import DAG
from airflow.operators.python import PythonOperator
from compute_acteurs.tasks.business_logic import compute_acteur
from utils import logging_utils as log

logger = logging.getLogger(__name__)


def compute_acteur_task(dag: DAG) -> PythonOperator:
    return PythonOperator(
        task_id="compute_acteur",
        python_callable=compute_acteur_wrapper,
        dag=dag,
    )


def compute_acteur_wrapper(**kwargs):
    df_acteur = kwargs["ti"].xcom_pull(task_ids="load_acteur")
    df_revisionacteur = kwargs["ti"].xcom_pull(task_ids="load_revisionacteur")

    log.preview("df_acteur", df_acteur)
    log.preview("df_revisionacteur", df_revisionacteur)

    return compute_acteur(df_acteur=df_acteur, df_revisionacteur=df_revisionacteur)
