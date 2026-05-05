import hashlib
import logging

from airflow import DAG
from airflow.providers.standard.operators.python import PythonOperator
from sources.config.tasks import TASKS
from sources.config.xcoms import XCOMS, xcom_pull, xcom_push
from sources.tasks.business_logic.db_data_prepare import db_data_prepare
from utils import logging_utils as log
from utils.db_tmp_tables import create_temporary_table

logger = logging.getLogger(__name__)


def db_data_prepare_task(dag: DAG) -> PythonOperator:
    return PythonOperator(
        task_id=TASKS.DB_DATA_PREPARE,
        python_callable=db_data_prepare_wrapper,
        dag=dag,
    )


def db_data_prepare_wrapper(ti, dag, params):
    df_acteur_from_source = xcom_pull(ti, XCOMS.DF_ACTEUR_FROM_SOURCE)
    df_acteur_from_db = xcom_pull(ti, XCOMS.DF_ACTEUR_FROM_DB)

    log.preview("df_acteur", df_acteur_from_source)
    log.preview("df_acteur_from_db", df_acteur_from_db)

    # Call the business logic function to prepare the DataFrames
    result = db_data_prepare(
        df_acteur=df_acteur_from_source,
        df_acteur_from_db=df_acteur_from_db,
    )

    # Generate a prefix to store temporary tables in the database
    # Short prefix : tmp_ + hash (max 12 characters total)
    run_id_hash = hashlib.md5(ti.run_id.encode()).hexdigest()[:8]
    table_prefix = f"tmp_{run_id_hash}"

    # Create temporary tables for each DataFrame
    table_name_create = f"{table_prefix}_acteur_to_create"
    table_name_update = f"{table_prefix}_acteur_to_update"
    table_name_delete = f"{table_prefix}_acteur_to_delete"

    # Create temporary tables for each DataFrame
    create_temporary_table(result["df_acteur_to_create"], table_name_create)
    create_temporary_table(result["df_acteur_to_update"], table_name_update)
    create_temporary_table(result["df_acteur_to_delete"], table_name_delete)

    # Push the names of the temporary tables into XCom instead of the DataFrames
    xcom_push(ti, key=XCOMS.TABLE_NAME_CREATE, value=table_name_create)
    xcom_push(ti, key=XCOMS.TABLE_NAME_UPDATE, value=table_name_update)
    xcom_push(ti, key=XCOMS.TABLE_NAME_DELETE, value=table_name_delete)
    xcom_push(ti, key=XCOMS.METADATA_TO_UPDATE, value=result["metadata_to_update"])
    xcom_push(ti, key=XCOMS.METADATA_TO_CREATE, value=result["metadata_to_create"])
    xcom_push(ti, key=XCOMS.METADATA_TO_DELETE, value=result["metadata_to_delete"])
