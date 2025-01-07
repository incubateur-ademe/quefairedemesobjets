import pandas as pd
from airflow import DAG
from airflow.operators.python import PythonOperator
from clustering.tasks.business_logic.clustering_db_data_read_acteurs import (
    clustering_db_data_read_acteurs,
)
from shared.tasks.database_logic.db_manager import PostgresConnectionManager
from utils import logging_utils as log


def clustering_db_data_read_acteurs_wrapper(**kwargs) -> pd.DataFrame:

    # use xcom to get the params from the previous task
    params = kwargs["ti"].xcom_pull(
        key="params", task_ids="clustering_acteur_config_validate"
    )

    log.preview("paramètres reçus", params)
    log.preview("sources sélectionnées", params["include_source_ids"])
    log.preview("acteur_types sélectionnés", params["include_acteur_type_ids"])
    log.preview("inclure si champs remplis", params["include_if_all_fields_filled"])
    log.preview("exclude si champs remplis", params["exclude_if_any_field_filled"])

    df, query = clustering_db_data_read_acteurs(
        include_source_ids=params["include_source_ids"],
        include_acteur_type_ids=params["include_acteur_type_ids"],
        include_if_all_fields_filled=params["include_if_all_fields_filled"],
        exclude_if_any_field_filled=params["exclude_if_any_field_filled"],
        engine=PostgresConnectionManager().engine,
    )
    log.preview("requête SQL utilisée", query)
    log.preview("acteurs sélectionnés", df)
    log.preview("# acteurs par source_id", df.groupby("source_id").size())
    log.preview("# acteurs par acteur_type_id", df.groupby("acteur_type_id").size())

    return df


def clustering_db_data_read_acteurs_task(dag: DAG) -> PythonOperator:
    """La tâche Airflow qui ne fait que appeler le wrapper"""
    return PythonOperator(
        task_id="clustering_db_data_read_acteurs",
        python_callable=clustering_db_data_read_acteurs_wrapper,
        dag=dag,
    )
