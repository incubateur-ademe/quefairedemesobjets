import logging

from airflow import DAG
from airflow.providers.standard.operators.python import PythonOperator
from sources.config.tasks import TASKS
from sources.config.xcoms import XCOMS, xcom_pull
from utils.db_tmp_tables import drop_temporary_table

logger = logging.getLogger(__name__)


def db_clean_temporary_tables_task(dag: DAG) -> PythonOperator:
    return PythonOperator(
        task_id=TASKS.DB_CLEAN_TEMPORARY_TABLES,
        python_callable=db_clean_temporary_tables_wrapper,
        dag=dag,
    )


def db_clean_temporary_tables_wrapper(ti) -> None:
    table_name_create = xcom_pull(ti, XCOMS.TABLE_NAME_CREATE)
    table_name_delete = xcom_pull(ti, XCOMS.TABLE_NAME_DELETE)
    table_name_update = xcom_pull(ti, XCOMS.TABLE_NAME_UPDATE)

    for table_name in (table_name_create, table_name_delete, table_name_update):
        if table_name:
            drop_temporary_table(table_name)
