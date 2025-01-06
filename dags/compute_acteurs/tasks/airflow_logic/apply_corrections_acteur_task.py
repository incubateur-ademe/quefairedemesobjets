import logging

from airflow import DAG
from airflow.operators.python import PythonOperator
from compute_acteurs.tasks.business_logic import apply_corrections_acteur
from shared.tasks.database_logic.db_manager import PostgresConnectionManager
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

    # get dag_run_id from kwargs
    dag_id = kwargs["dag_run"].dag_id
    dag_run_id = kwargs["dag_run"].run_id
    # get task id
    task_id = kwargs["task_instance"].task_id

    log.preview("df_acteur", df_acteur)
    log.preview("df_revisionacteur", df_revisionacteur)
    log.preview("dag_id", dag_id)
    log.preview("dag_run_id", dag_run_id)

    result = apply_corrections_acteur(
        df_acteur=df_acteur, df_revisionacteur=df_revisionacteur
    )
    db_manager = PostgresConnectionManager()
    db_manager.write_data_xcom(
        dag_id=dag_id,
        dag_run_id=dag_run_id,
        task_id=task_id,
        dataset_name="df_acteur_merged",
        df=result["df_acteur_merged"],
    )
    db_manager.write_data_xcom(
        dag_id=dag_id,
        dag_run_id=dag_run_id,
        task_id=task_id,
        dataset_name="df_children",
        df=result["df_children"],
    )
    # {
    #     "df_acteur_merged": df_acteur_merged,
    #     # ["parent_id", "child_id", "child_source_id"]
    #     "df_children": df_children
    # }
    return result
