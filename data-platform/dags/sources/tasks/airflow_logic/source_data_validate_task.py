import logging

from airflow import DAG
from airflow.providers.standard.operators.python import PythonOperator
from airflow.task.trigger_rule import TriggerRule
from sources.tasks.airflow_logic.config_management import DAGConfig
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
    dag_config = DAGConfig.from_airflow_params(kwargs["params"])

    log.preview("df before validation", df)
    log.preview("DAG parameters", dag_config)

    return source_data_validate(df=df, dag_config=dag_config)
