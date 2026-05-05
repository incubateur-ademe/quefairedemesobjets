import logging

import pandas as pd
from airflow import DAG
from airflow.providers.standard.operators.python import PythonOperator
from airflow.task.trigger_rule import TriggerRule
from shared.tasks.database_logic.db_manager import PostgresConnectionManager
from sources.config.models import SourceConfig
from sources.config.tasks import TASKS
from sources.tasks.business_logic.source_config_validate import source_config_validate
from utils import logging_utils as log

logger = logging.getLogger(__name__)


def source_config_validate_task(dag: DAG) -> PythonOperator:
    return PythonOperator(
        task_id=TASKS.SOURCE_CONFIG_VALIDATE,
        python_callable=source_config_validate_wrapper,
        dag=dag,
        trigger_rule=TriggerRule.ALL_SUCCESS,
        retries=0,
    )


def source_config_validate_wrapper(ti, dag, params) -> None:
    engine = PostgresConnectionManager().engine
    dag_config = SourceConfig.from_airflow_params(params)

    codes_sc_db = set(
        pd.read_sql_table("qfdmo_souscategorieobjet", engine, columns=["code"])[
            "code"
        ].unique()
    )

    log.preview("paramètres du DAG", dag_config)
    log.preview("codes sous-catégories DB", codes_sc_db)

    source_config_validate(
        dag_config=dag_config,
        codes_sc_db=codes_sc_db,
    )
