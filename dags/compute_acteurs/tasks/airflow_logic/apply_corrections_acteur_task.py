import logging

from airflow import DAG
from airflow.operators.python import PythonOperator
from compute_acteurs.tasks.business_logic import apply_corrections_acteur
from utils import logging_utils as log

logger = logging.getLogger(__name__)


def apply_corrections_acteur_task(dag: DAG) -> PythonOperator:
    return PythonOperator(
        task_id="apply_corrections_acteur",
        python_callable=apply_corrections_acteur_wrapper,
        dag=dag,
    )


def apply_corrections_acteur_wrapper(**kwargs):
    df_acteur = kwargs["ti"].xcom_pull(task_ids="load_acteur")
    df_revisionacteur = kwargs["ti"].xcom_pull(task_ids="load_revisionacteur")

    log.preview("df_acteur", df_acteur)
    log.preview("df_revisionacteur", df_revisionacteur)

    return apply_corrections_acteur(
        df_acteur=df_acteur, df_revisionacteur=df_revisionacteur
    )
