import logging

from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.utils.trigger_rule import TriggerRule
from sources.tasks.business_logic.source_data_validate import source_data_validate
from utils import logging_utils as log

logger = logging.getLogger(__name__)


def source_data_validate_task(dag: DAG) -> PythonOperator:
    return PythonOperator(
        task_id="source_data_validate",
        python_callable=source_data_validate_wrapper,
        dag=dag,
        trigger_rule=TriggerRule.ALL_SUCCESS,
        retries=0,
    )


def source_data_validate_wrapper(**kwargs) -> None:
    df = kwargs["ti"].xcom_pull(task_ids="source_data_normalize")
    params = kwargs["params"]

    log.preview("df depuis source_data_normalize", df)
    log.preview("paramètres du DAG", params)

    return source_data_validate(
        df=df,
        params=params,
    )
