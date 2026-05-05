import logging

from airflow import DAG
from airflow.providers.standard.operators.python import PythonOperator
from airflow.task.trigger_rule import TriggerRule
from sources.config.models import SourceConfig
from sources.config.tasks import TASKS
from sources.config.xcoms import XCOMS, xcom_pull
from sources.tasks.business_logic.source_data_validate import source_data_validate
from utils import logging_utils as log

logger = logging.getLogger(__name__)


def source_data_validate_task(dag: DAG) -> PythonOperator:
    return PythonOperator(
        task_id=TASKS.SOURCE_DATA_VALIDATE,
        python_callable=source_data_validate_wrapper,
        dag=dag,
        trigger_rule=TriggerRule.ALL_SUCCESS,
        retries=0,
    )


def source_data_validate_wrapper(ti, dag, params) -> None:
    df = xcom_pull(ti, XCOMS.SOURCE_NORMALIZED)
    dag_config = SourceConfig.from_airflow_params(params)

    log.preview("df before validation", df)
    log.preview("DAG parameters", dag_config)

    source_data_validate(df=df, dag_config=dag_config)
