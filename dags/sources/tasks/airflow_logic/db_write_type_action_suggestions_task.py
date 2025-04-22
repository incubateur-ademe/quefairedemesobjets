import logging

from airflow import DAG
from airflow.operators.python import PythonOperator
from sources.tasks.business_logic.db_write_type_action_suggestions import (
    db_write_type_action_suggestions,
)
from utils import logging_utils as log

logger = logging.getLogger(__name__)


def db_write_type_action_suggestions_task(dag: DAG) -> PythonOperator:
    return PythonOperator(
        task_id="db_write_suggestion",
        python_callable=db_write_type_action_suggestions_wrapper,
        dag=dag,
    )


def db_write_type_action_suggestions_wrapper(**kwargs) -> None:
    dag_name = kwargs["dag"].dag_display_name or kwargs["dag"].dag_id
    run_id = kwargs["run_id"]
    dfs_acteur = kwargs["ti"].xcom_pull(task_ids="db_data_prepare")
    df_acteur_to_delete = dfs_acteur["df_acteur_to_delete"]
    df_acteur_to_create = dfs_acteur["df_acteur_to_create"]
    df_acteur_to_update = dfs_acteur["df_acteur_to_update"]
    metadata = kwargs["ti"].xcom_pull(task_ids="source_data_normalize", key="metadata")
    metadata_columns_updated = kwargs["ti"].xcom_pull(
        task_ids="keep_acteur_changed", key="metadata_columns_updated"
    )

    log.preview("dag_name", dag_name)
    log.preview("run_id", run_id)
    log.preview("df_acteur_to_delete", df_acteur_to_delete)
    log.preview("df_acteur_to_create", df_acteur_to_create)
    log.preview("df_acteur_to_update", df_acteur_to_update)

    if (
        df_acteur_to_create.empty
        and df_acteur_to_delete.empty
        and df_acteur_to_update.empty
    ):
        logger.warning("!!! Aucune suggestion à traiter pour cette source !!!")
        # set the task to airflow skip status
        kwargs["ti"].xcom_push(key="skip", value=True)
        return

    return db_write_type_action_suggestions(
        dag_name=dag_name,
        run_id=run_id,
        df_acteur_to_create=df_acteur_to_create,
        df_acteur_to_delete=df_acteur_to_delete,
        df_acteur_to_update=df_acteur_to_update,
        metadata_to_create=metadata,
        metadata_to_update={**metadata, **metadata_columns_updated},
        metadata_to_delete=metadata,
    )
