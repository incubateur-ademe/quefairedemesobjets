import logging

import pandas as pd
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.utils.trigger_rule import TriggerRule
from sources.tasks.airflow_logic.config_management import get_nested_config_parameter
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

    params = kwargs["params"]
    source_code = params.get("source_code")
    column_mapping = params.get("column_mapping", {})
    column_transformations = params.get("column_transformations", [])
    column_transformations = get_nested_config_parameter(column_transformations)
    columns_to_add_by_default = params.get("columns_to_add_by_default", {})
    label_bonus_reparation = params.get("label_bonus_reparation")
    validate_address_with_ban = params.get("validate_address_with_ban", False)
    ignore_duplicates = params.get("ignore_duplicates", False)
    combine_columns_categories = params.get("combine_columns_categories", [])
    merge_duplicated_acteurs = params.get("merge_duplicated_acteurs", False)
    product_mapping = params.get("product_mapping", {})
    dechet_mapping = params.get("dechet_mapping", {})
    acteurtype_id_by_code = read_mapping_from_postgres(table_name="qfdmo_acteurtype")
    source_id_by_code = read_mapping_from_postgres(table_name="qfdmo_source")
    source_code_prefix = params.get("source_code_prefix")

    log.preview("df avant normalisation", df)
    log.preview("source_code", source_code)
    log.preview("column_mapping", column_mapping)
    log.preview("column_transformations", column_transformations)
    log.preview("columns_to_add_by_default", columns_to_add_by_default)
    log.preview("label_bonus_reparation", label_bonus_reparation)
    log.preview("validate_address_with_ban", validate_address_with_ban)
    log.preview("ignore_duplicates", ignore_duplicates)
    log.preview("combine_columns_categories", combine_columns_categories)
    log.preview("merge_duplicated_acteurs", merge_duplicated_acteurs)
    log.preview("product_mapping", product_mapping)
    log.preview("dechet_mapping", dechet_mapping)
    log.preview("acteurtype_id_by_code", acteurtype_id_by_code)
    log.preview("source_id_by_code", source_id_by_code)
    log.preview("source_code_prefix", source_code_prefix)

    params = kwargs["params"]

    return source_data_normalize(
        df_acteur_from_source=df,
        source_code=source_code,
        column_mapping=column_mapping,
        column_transformations=column_transformations,
        columns_to_add_by_default=columns_to_add_by_default,
        label_bonus_reparation=label_bonus_reparation,
        validate_address_with_ban=validate_address_with_ban,
        ignore_duplicates=ignore_duplicates,
        combine_columns_categories=combine_columns_categories,
        merge_duplicated_acteurs=merge_duplicated_acteurs,
        product_mapping=product_mapping,
        dechet_mapping=dechet_mapping,
        acteurtype_id_by_code=acteurtype_id_by_code,
        source_id_by_code=source_id_by_code,
        source_code_prefix=source_code_prefix,
    )
