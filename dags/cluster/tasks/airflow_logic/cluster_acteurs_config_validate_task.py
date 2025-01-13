"""
Tâche Airflow pour valider la configuration de clustering
"""

import logging

from airflow import DAG
from airflow.operators.python import PythonOperator
from cluster.tasks.business_logic.cluster_acteurs_config_validate import (
    cluster_acteurs_config_validate,
)
from sources.tasks.business_logic.read_mapping_from_postgres import (
    read_mapping_from_postgres,
)
from utils import logging_utils as log

logger = logging.getLogger(__name__)


mapping_source_id_by_code = read_mapping_from_postgres(table_name="qfdmo_source")
mapping_acteur_type_id_by_code = read_mapping_from_postgres(
    table_name="qfdmo_acteurtype"
)


def task_info_get():
    return """


    ============================================================
    Description de la tâche "cluster_acteurs_config_validate"
    ============================================================

    💡 quoi: valide la configuration fournie par la UI (+ défauts si il y en a)

    🎯 pourquoi: échouer au plus tôt si il y a des problèmes de conf et ne pas
        faire du traitement de données inutile

    🏗️ comment: en comparant la config fournie avec des règles censées
        s'aligner avec les besoins métier (ex: prérequis)
        et la UI (ex: optionalité)
    """


def cluster_acteurs_config_validate_wrapper(**kwargs) -> None:
    """Wrapper de la tâche Airflow pour échanger les paramètres
    et pouvoir tester la tâche sans mock."""
    logger.info(task_info_get())

    params = kwargs["params"]

    for key, value in params.items():
        log.preview(f"param: {key}", value)

    if (
        len(params["include_source_codes"]) == 1
        and not params["cluster_intra_source_is_allowed"]
    ):
        raise ValueError("Clustering intra-source désactivé mais une 1 source incluse")

    include_source_ids, include_acteur_type_ids = cluster_acteurs_config_validate(
        mapping_source_id_by_code=mapping_source_id_by_code,
        mapping_acteur_type_id_by_code=mapping_acteur_type_id_by_code,
        include_source_codes=params["include_source_codes"] or [],
        include_acteur_type_codes=params["include_acteur_type_codes"] or [],
        include_if_all_fields_filled=params["include_if_all_fields_filled"] or [],
        exclude_if_any_field_filled=params["exclude_if_any_field_filled"] or [],
    )
    params["include_source_ids"] = include_source_ids
    params["include_acteur_type_ids"] = include_acteur_type_ids

    kwargs["ti"].xcom_push(key="params", value=params)


def cluster_acteurs_config_validate_task(dag: DAG) -> PythonOperator:
    """La tâche Airflow qui ne fait que appeler le wrapper"""
    return PythonOperator(
        task_id="cluster_acteurs_config_validate",
        python_callable=cluster_acteurs_config_validate_wrapper,
        dag=dag,
    )
