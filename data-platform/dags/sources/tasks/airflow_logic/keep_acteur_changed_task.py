import logging

from airflow import DAG
from airflow.providers.standard.operators.python import PythonOperator
from sources.config.models import SourceConfig
from sources.config.tasks import TASKS
from sources.config.xcoms import XCOMS, xcom_pull, xcom_push
from sources.tasks.business_logic.db_read_acteur import db_read_acteur
from sources.tasks.business_logic.keep_acteur_changed import keep_acteur_changed
from utils import logging_utils as log

logger = logging.getLogger(__name__)


def keep_acteur_changed_task(dag: DAG) -> PythonOperator:
    return PythonOperator(
        task_id=TASKS.KEEP_ACTEUR_CHANGED,
        python_callable=keep_acteur_changed_wrapper,
        dag=dag,
    )


def keep_acteur_changed_wrapper(ti, dag, params):
    df_normalized = xcom_pull(ti, XCOMS.SOURCE_NORMALIZED)
    dag_config = SourceConfig.from_airflow_params(params)

    df_acteur_from_db = db_read_acteur(
        df_normalized=df_normalized,
        dag_config=dag_config,
    )

    log.preview("df_normalized", df_normalized)
    log.preview("df_acteur_from_db", df_acteur_from_db)
    log.preview("dag_config", dag_config)

    df_acteur_from_source, df_acteur_from_db, metadata_columns_updated = (
        keep_acteur_changed(
            df_normalized=df_normalized,
            df_acteur_from_db=df_acteur_from_db,
            dag_config=dag_config,
        )
    )
    xcom_push(ti, key=XCOMS.DF_ACTEUR_FROM_SOURCE, value=df_acteur_from_source)
    xcom_push(ti, key=XCOMS.DF_ACTEUR_FROM_DB, value=df_acteur_from_db)
    xcom_push(ti, key=XCOMS.METADATA_COLUMNS_UPDATED, value=metadata_columns_updated)
