import logging

import pandas as pd
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.providers.postgres.hooks.postgres import PostgresHook
from airflow.utils.trigger_rule import TriggerRule
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
    params = kwargs["params"]
    engine = PostgresHook(postgres_conn_id="qfdmo_django_db").get_sqlalchemy_engine()
    codes_sc_db = set(
        pd.read_sql_table("qfdmo_souscategorieobjet", engine, columns=["code"])[
            "code"
        ].unique()
    )

    log.preview("paramètres du DAG", params)
    log.preview("codes sous-catégories DB", codes_sc_db)

    return source_config_validate(
        params=params,
        codes_sc_db=codes_sc_db,
    )
