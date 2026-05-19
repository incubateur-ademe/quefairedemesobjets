import logging

from airflow import DAG
from airflow.providers.standard.operators.python import PythonOperator
from airflow.task.trigger_rule import TriggerRule
from sources.config.models import SourceConfig
from sources.config.tasks import TASKS
from sources.config.xcoms import XCOMS, xcom_pull, xcom_push
from sources.tasks.business_logic.source_data_normalize import source_data_normalize
from utils import logging_utils as log

logger = logging.getLogger(__name__)


def source_data_normalize_task(dag: DAG) -> PythonOperator:
    return PythonOperator(
        task_id=TASKS.SOURCE_DATA_NORMALIZE,
        python_callable=source_data_normalize_wrapper,
        dag=dag,
        trigger_rule=TriggerRule.ALL_SUCCESS,
        retries=0,
    )


def source_data_normalize_wrapper(ti, dag, params) -> None:
    df = xcom_pull(ti, XCOMS.SOURCE_DOWNLOADED)

    dag_config = SourceConfig.from_airflow_params(params)
    dag_id = dag.dag_id

    log.preview("df avant normalisation", df)
    log.preview("paramètres du DAG", dag_config)
    log.preview("ID du DAG", dag_id)

    df, df_log_error, df_log_warning, metadata = source_data_normalize(
        df_acteur_from_source=df,
        dag_config=dag_config,
        dag_id=dag_id,
    )

    log.preview("df après normalisation", df)
    log.preview("df_log_error", df_log_error)
    log.preview("df_log_warning", df_log_warning)
    log.preview("metadata", metadata)

    xcom_push(ti, key=XCOMS.METADATA, value=metadata)
    xcom_push(ti, key=XCOMS.DF_LOG_ERROR, value=df_log_error)
    xcom_push(ti, key=XCOMS.DF_LOG_WARNING, value=df_log_warning)

    xcom_push(ti, key=XCOMS.SOURCE_NORMALIZED, value=df)
