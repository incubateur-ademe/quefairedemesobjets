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
    df = kwargs["ti"].xcom_pull(task_ids="source_data_normalize")
    df_acteurs = kwargs["ti"].xcom_pull(task_ids="db_read_acteur")

    params = kwargs["params"]
    column_to_drop = params.get("column_to_drop", [])

    log.preview("df (source_data_normalize)", df)
    log.preview("df_acteurs", df_acteurs)
    log.preview("column_to_drop", column_to_drop)

    return propose_acteur_changes(
        df=df,
        df_acteurs=df_acteurs,
        column_to_drop=column_to_drop,
    )
