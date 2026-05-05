import logging

from airflow import DAG
from airflow.providers.standard.operators.python import PythonOperator
from sources.config.models import SourceConfig
from sources.config.tasks import TASKS
from sources.config.xcoms import XCOMS, xcom_pull, xcom_push
from sources.tasks.business_logic.db_write_type_action_suggestions import (
    db_write_type_action_suggestions,
)
from utils import logging_utils as log
from utils.db_tmp_tables import read_and_drop_temporary_table

logger = logging.getLogger(__name__)


def db_write_type_action_suggestions_task(dag: DAG) -> PythonOperator:
    return PythonOperator(
        task_id=TASKS.DB_WRITE_TYPE_ACTION_SUGGESTIONS,
        python_callable=db_write_type_action_suggestions_wrapper,
        dag=dag,
    )


def db_write_type_action_suggestions_wrapper(ti, dag, params) -> None:
    dag_name = dag.dag_display_name or dag.dag_id
    dag_config = SourceConfig.from_airflow_params(params)

    run_id = ti.run_id

    # Récupérer les noms des tables temporaires depuis XCom
    table_name_create = xcom_pull(ti, XCOMS.TABLE_NAME_CREATE)
    table_name_delete = xcom_pull(ti, XCOMS.TABLE_NAME_DELETE)
    table_name_update = xcom_pull(ti, XCOMS.TABLE_NAME_UPDATE)

    # Load the DataFrames from the temporary tables
    df_acteur_to_create = read_and_drop_temporary_table(table_name_create)
    df_acteur_to_delete = read_and_drop_temporary_table(table_name_delete)
    df_acteur_to_update = read_and_drop_temporary_table(table_name_update)

    metadata_to_create = xcom_pull(ti, XCOMS.METADATA_TO_CREATE)
    metadata_to_update = xcom_pull(ti, XCOMS.METADATA_TO_UPDATE)
    metadata_to_delete = xcom_pull(ti, XCOMS.METADATA_TO_DELETE)

    metadata = xcom_pull(ti, XCOMS.METADATA)
    df_log_error = xcom_pull(ti, XCOMS.DF_LOG_ERROR)
    df_log_warning = xcom_pull(ti, XCOMS.DF_LOG_WARNING)
    metadata_columns_updated = xcom_pull(ti, XCOMS.METADATA_COLUMNS_UPDATED)

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
        xcom_push(ti, key=XCOMS.SKIP, value=True)
        return

    db_write_type_action_suggestions(
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
        use_legacy_suggestions=dag_config.use_legacy_suggestions,
    )
