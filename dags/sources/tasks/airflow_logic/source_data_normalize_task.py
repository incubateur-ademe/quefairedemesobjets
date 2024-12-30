import logging

import pandas as pd
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.utils.trigger_rule import TriggerRule
from sources.tasks.airflow_logic.config_management import DAGConfig
from sources.tasks.business_logic.read_mapping_from_postgres import (
    read_mapping_from_postgres,
)
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
    # source_code = params.get("source_code")
    # column_mapping = params.get("column_mapping", {})
    # column_transformations = params.get("column_transformations", [])
    # column_transformations = get_nested_config_parameter(column_transformations)
    # columns_to_add_by_default = params.get("columns_to_add_by_default", {})
    # label_bonus_reparation = params.get("label_bonus_reparation")
    # validate_address_with_ban = params.get("validate_address_with_ban", False)
    # ignore_duplicates = params.get("ignore_duplicates", False)
    # combine_columns_categories = params.get("combine_columns_categories", [])
    # merge_duplicated_acteurs = params.get("merge_duplicated_acteurs", False)
    # product_mapping = params.get("product_mapping", {})
    # dechet_mapping = params.get("dechet_mapping", {})
    acteurtype_id_by_code = read_mapping_from_postgres(table_name="qfdmo_acteurtype")
    source_id_by_code = read_mapping_from_postgres(table_name="qfdmo_source")

    log.preview("df avant normalisation", df)
    log.preview("paramètres du DAG", dag_config)
    log.preview("acteurtype_id_by_code", acteurtype_id_by_code)
    log.preview("source_id_by_code", source_id_by_code)

    return source_data_normalize(
        df_acteur_from_source=df,
        dag_config=dag_config,
        acteurtype_id_by_code=acteurtype_id_by_code,
        source_id_by_code=source_id_by_code,
    )
