import logging

from airflow import DAG
from airflow.operators.python import PythonOperator
from sources.tasks.business_logic.db_write_type_action_suggestions import (
    db_write_type_action_suggestions,
    db_write_type_action_suggestions_v2,
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
    df_acteur_to_create = kwargs["ti"].xcom_pull(
        task_ids="db_data_prepare", key="df_acteur_to_create"
    )
    df_acteur_to_delete = kwargs["ti"].xcom_pull(
        task_ids="db_data_prepare", key="df_acteur_to_delete"
    )
    df_acteur_to_update = kwargs["ti"].xcom_pull(
        task_ids="db_data_prepare", key="df_acteur_to_update"
    )

    metadata_to_create = kwargs["ti"].xcom_pull(
        task_ids="db_data_prepare", key="metadata_to_create"
    )
    metadata_to_update = kwargs["ti"].xcom_pull(
        task_ids="db_data_prepare", key="metadata_to_update"
    )
    metadata_to_delete = kwargs["ti"].xcom_pull(
        task_ids="db_data_prepare", key="metadata_to_delete"
    )

    metadata = kwargs["ti"].xcom_pull(task_ids="source_data_normalize", key="metadata")
    df_log_error = kwargs["ti"].xcom_pull(
        task_ids="source_data_normalize", key="df_log_error"
    )
    df_log_warning = kwargs["ti"].xcom_pull(
        task_ids="source_data_normalize", key="df_log_warning"
    )
    metadata_columns_updated = kwargs["ti"].xcom_pull(
        task_ids="keep_acteur_changed", key="metadata_columns_updated"
    )

    log.preview("dag_name", dag_name)
    log.preview("run_id", run_id)
    log.preview("df_acteur_to_delete", df_acteur_to_delete)
    log.preview("df_acteur_to_create", df_acteur_to_create)
    log.preview("df_acteur_to_update", df_acteur_to_update)
    log.preview("df_log_error", df_log_error)
    log.preview("df_log_warning", df_log_warning)

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
        metadata_to_create={**metadata, **metadata_to_create},
        metadata_to_update={
            **metadata,
            **metadata_to_update,
            **metadata_columns_updated,
        },
        metadata_to_delete={**metadata, **metadata_to_delete},
        df_log_error=df_log_error,
        df_log_warning=df_log_warning,
    )


def db_write_type_action_suggestions_v2_task(dag: DAG) -> PythonOperator:
    return PythonOperator(
        task_id="db_write_suggestion_v2",
        python_callable=db_write_type_action_suggestions_v2_wrapper,
        dag=dag,
    )


def db_write_type_action_suggestions_v2_wrapper(**kwargs) -> None:
    dag_name = kwargs["dag"].dag_display_name or kwargs["dag"].dag_id
    run_id = kwargs["run_id"]
    df_acteur_to_create = kwargs["ti"].xcom_pull(
        task_ids="db_data_prepare", key="df_acteur_to_create"
    )
    df_acteur_to_delete = kwargs["ti"].xcom_pull(
        task_ids="db_data_prepare", key="df_acteur_to_delete"
    )
    df_acteur_to_update = kwargs["ti"].xcom_pull(
        task_ids="db_data_prepare", key="df_acteur_to_update"
    )

    metadata_to_create = kwargs["ti"].xcom_pull(
        task_ids="db_data_prepare", key="metadata_to_create"
    )
    metadata_to_update = kwargs["ti"].xcom_pull(
        task_ids="db_data_prepare", key="metadata_to_update"
    )
    metadata_to_delete = kwargs["ti"].xcom_pull(
        task_ids="db_data_prepare", key="metadata_to_delete"
    )

    metadata = kwargs["ti"].xcom_pull(task_ids="source_data_normalize", key="metadata")
    df_log_error = kwargs["ti"].xcom_pull(
        task_ids="source_data_normalize", key="df_log_error"
    )
    df_log_warning = kwargs["ti"].xcom_pull(
        task_ids="source_data_normalize", key="df_log_warning"
    )
    metadata_columns_updated = kwargs["ti"].xcom_pull(
        task_ids="keep_acteur_changed", key="metadata_columns_updated"
    )

    log.preview("dag_name", dag_name)
    log.preview("run_id", run_id)
    log.preview("df_acteur_to_delete", df_acteur_to_delete)
    log.preview("df_acteur_to_create", df_acteur_to_create)
    log.preview("df_acteur_to_update", df_acteur_to_update)
    log.preview("df_log_error", df_log_error)
    log.preview("df_log_warning", df_log_warning)

    if (
        df_acteur_to_create.empty
        and df_acteur_to_delete.empty
        and df_acteur_to_update.empty
    ):
        logger.warning("!!! Aucune suggestion à traiter pour cette source !!!")
        # set the task to airflow skip status
        kwargs["ti"].xcom_push(key="skip", value=True)
        return

    return db_write_type_action_suggestions_v2(
        dag_name=dag_name,
        run_id=run_id,
        df_acteur_to_create=df_acteur_to_create,
        df_acteur_to_delete=df_acteur_to_delete,
        df_acteur_to_update=df_acteur_to_update,
        metadata_to_create={**metadata, **metadata_to_create},
        metadata_to_update={
            **metadata,
            **metadata_to_update,
            **metadata_columns_updated,
        },
        metadata_to_delete={**metadata, **metadata_to_delete},
        df_log_error=df_log_error,
        df_log_warning=df_log_warning,
    )
