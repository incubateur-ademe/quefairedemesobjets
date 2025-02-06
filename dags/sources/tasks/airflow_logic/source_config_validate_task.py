import logging

import pandas as pd
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.utils.trigger_rule import TriggerRule
from shared.tasks.database_logic.db_manager import PostgresConnectionManager
from sources.tasks.airflow_logic.config_management import DAGConfig
from sources.tasks.business_logic.source_config_validate import source_config_validate
from utils import logging_utils as log

logger = logging.getLogger(__name__)


def source_config_validate_task(dag: DAG) -> PythonOperator:
    return PythonOperator(
        task_id="source_config_validate",
        python_callable=source_config_validate_wrapper,
        dag=dag,
        trigger_rule=TriggerRule.ALL_SUCCESS,
        retries=0,
    )


def source_config_validate_wrapper(**kwargs) -> None:
    engine = PostgresConnectionManager().engine
    dag_config = DAGConfig.from_airflow_params(kwargs["params"])

    codes_sc_db = set(
        pd.read_sql_table("qfdmo_souscategorieobjet", engine, columns=["code"])[
            "code"
        ].unique()
    )

    log.preview("paramètres du DAG", dag_config)
    log.preview("codes sous-catégories DB", codes_sc_db)

    return source_config_validate(
        dag_config=dag_config,
        codes_sc_db=codes_sc_db,
    )
