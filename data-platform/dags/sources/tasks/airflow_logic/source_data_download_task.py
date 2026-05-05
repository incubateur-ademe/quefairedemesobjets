import logging

from airflow import DAG
from airflow.providers.standard.operators.python import PythonOperator
from airflow.task.trigger_rule import TriggerRule
from sources.config.models import SourceConfig
from sources.config.tasks import TASKS
from sources.config.xcoms import XCOMS, xcom_push
from sources.tasks.business_logic.source_data_download import source_data_download
from utils import logging_utils as log

logger = logging.getLogger(__name__)


def source_data_download_task(dag: DAG) -> PythonOperator:
    return PythonOperator(
        task_id=TASKS.SOURCE_DATA_DOWNLOAD,
        python_callable=source_data_download_wrapper,
        dag=dag,
        trigger_rule=TriggerRule.ALL_SUCCESS,
        retries=0,
    )


def source_data_download_wrapper(ti, dag, params):
    dag_config = SourceConfig.from_airflow_params(params)
    endpoint = dag_config.endpoint
    metadata_endpoint = dag_config.metadata_endpoint
    s3_connection_id = dag_config.s3_connection_id

    log.preview("API end point", endpoint)
    if s3_connection_id:
        log.preview("S3 connection id", s3_connection_id)

    df = source_data_download(
        endpoint=endpoint,
        s3_connection_id=s3_connection_id,
        metadata_endpoint=metadata_endpoint,
    )

    xcom_push(ti, XCOMS.SOURCE_DOWNLOADED, df)
