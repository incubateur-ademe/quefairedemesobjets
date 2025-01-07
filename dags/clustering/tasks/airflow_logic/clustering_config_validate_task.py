"""
Tâche Airflow pour valider la configuration de clustering
"""

from airflow import DAG
from airflow.operators.python import PythonOperator
from clustering.tasks.business_logic.clustering_config_validate import (
    clustering_acteur_config_validate,
)
from sources.tasks.business_logic.read_mapping_from_postgres import (
    read_mapping_from_postgres,
)
from utils import logging_utils as log

mapping_source_id_by_code = read_mapping_from_postgres(table_name="qfdmo_source")
mapping_acteur_type_id_by_code = read_mapping_from_postgres(
    table_name="qfdmo_acteurtype"
)


def clustering_acteur_config_validate_wrapper(**kwargs) -> None:
    """Wrapper de la tâche Airflow pour échanger les paramètres
    et pouvoir tester la tâche sans mock."""
    params = kwargs["params"]

    log.preview("sources sélectionnées", params["include_source_codes"])
    log.preview("acteur_types sélectionnés", params["include_acteur_type_codes"])
    log.preview("inclure si champs non-vide", params["include_if_all_fields_filled"])
    log.preview("exclude si champ vide", params["exclude_if_any_field_filled"])
    log.preview(
        "champs à la fois inclure/exclure", params["include_if_all_fields_filled"]
    )

    include_source_ids, include_acteur_type_ids = clustering_acteur_config_validate(
        mapping_source_id_by_code=mapping_source_id_by_code,
        mapping_acteur_type_id_by_code=mapping_acteur_type_id_by_code,
        include_source_codes=params["include_source_codes"],
        include_acteur_type_codes=params["include_acteur_type_codes"],
        include_if_all_fields_filled=params["include_if_all_fields_filled"],
        exclude_if_any_field_filled=params["exclude_if_any_field_filled"],
    )
    params["include_source_ids"] = include_source_ids
    params["include_acteur_type_ids"] = include_acteur_type_ids

    # Use xcom to pass the params to the next task
    kwargs["ti"].xcom_push(key="params", value=params)


def clustering_acteur_config_validate_task(dag: DAG) -> PythonOperator:
    """La tâche Airflow qui ne fait que appeler le wrapper"""
    return PythonOperator(
        task_id="clustering_acteur_config_validate",
        python_callable=clustering_acteur_config_validate_wrapper,
        dag=dag,
    )
