from airflow import DAG
from airflow.operators.python import PythonOperator
from sources.tasks.business_logic.propose_acteur_changes import propose_acteur_changes
from utils import logging_utils as log


def propose_acteur_changes_task(dag: DAG) -> PythonOperator:
    return PythonOperator(
        task_id="propose_acteur_changes",
        python_callable=propose_acteur_changes_wrapper,
        dag=dag,
    )


def propose_acteur_changes_wrapper(**kwargs):
    df_acteur = kwargs["ti"].xcom_pull(task_ids="source_data_normalize")
    df_acteur_from_db = kwargs["ti"].xcom_pull(task_ids="db_read_acteur")

    log.preview("df (source_data_normalize)", df_acteur)
    log.preview("df_acteurs", df_acteur_from_db)

    return propose_acteur_changes(
        df_acteur=df_acteur,
        df_acteur_from_db=df_acteur_from_db,
    )
