import logging

import pandas as pd
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.utils.trigger_rule import TriggerRule
from sources.tasks.airflow_logic.config_management import DAGConfig
from sources.tasks.business_logic.source_data_download import source_data_download
from utils import logging_utils as log

logger = logging.getLogger(__name__)


def source_data_download_task(dag: DAG) -> PythonOperator:
    return PythonOperator(
        task_id="source_data_download",
        python_callable=source_data_download_wrapper,
        dag=dag,
        trigger_rule=TriggerRule.ALL_SUCCESS,
        retries=0,
    )


def source_data_download_wrapper(**kwargs) -> pd.DataFrame:
    dag_config = DAGConfig.from_airflow_params(kwargs["params"])
    endpoint = dag_config.endpoint
    metadata_endpoint = dag_config.metadata_endpoint
    s3_connection_id = dag_config.s3_connection_id

    log.preview("API end point", endpoint)
    if s3_connection_id:
        log.preview("S3 connection id", s3_connection_id)

    return source_data_download(
        endpoint=endpoint,
        s3_connection_id=s3_connection_id,
        metadata_endpoint=metadata_endpoint,
    )
