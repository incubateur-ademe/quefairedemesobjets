import logging

import pandas as pd
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.utils.trigger_rule import TriggerRule
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
    params = kwargs["params"]
    endpoint = params["endpoint"]

    log.preview("API end point", endpoint)

    return source_data_download(endpoint=endpoint)
