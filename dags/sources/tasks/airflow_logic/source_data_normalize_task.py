import logging

import pandas as pd
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.utils.trigger_rule import TriggerRule
from sources.tasks.airflow_logic.config_management import DAGConfig
from sources.tasks.business_logic.source_data_normalize import source_data_normalize
from utils import logging_utils as log

logger = logging.getLogger(__name__)


def source_data_normalize_task(dag: DAG) -> PythonOperator:
    return PythonOperator(
        task_id="source_data_normalize",
        python_callable=source_data_normalize_wrapper,
        dag=dag,
        trigger_rule=TriggerRule.ALL_SUCCESS,
        retries=0,
    )


def source_data_normalize_wrapper(**kwargs) -> pd.DataFrame:
    df = kwargs["ti"].xcom_pull(task_ids="source_data_download")

    dag_config = DAGConfig.from_airflow_params(kwargs["params"])
    dag_id = kwargs["dag"].dag_id

    log.preview("df avant normalisation", df)
    log.preview("paramètres du DAG", dag_config)
    log.preview("ID du DAG", dag_id)

    return source_data_normalize(
        df_acteur_from_source=df,
        dag_config=dag_config,
        dag_id=dag_id,
    )
