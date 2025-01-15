import logging

from airflow import DAG
from airflow.operators.python import PythonOperator
from cluster.tasks.business_logic.cluster_acteurs_db_data_read_acteurs import (
    cluster_acteurs_db_data_read_acteurs,
)
from utils import logging_utils as log
from utils.django import django_setup_full

django_setup_full()

from qfdmo.models import DisplayedActeur  # noqa: E402

logger = logging.getLogger(__name__)


def task_info_get():
    return """


    ============================================================
    Description de la tâche "cluster_acteurs_db_data_read_acteurs"
    ============================================================

    💡 quoi: va chercher en base de données les acteurs correspondants
        aux critères d'inclusion et d'exclusion du DAG
         - ces acteurs "candidats" ne seront pas forcément utilisés
         dans des clusters

    🎯 pourquoi: c'est la donnée de base dont on a besoin pour le clustering

    🏗️ comment: constructions/execution d'une requête SQL sur la base
        des critrères d'inclusion/exclusion
    """


def cluster_acteurs_db_data_read_acteurs_wrapper(**kwargs) -> None:
    logger.info(task_info_get())

    # use xcom to get the params from the previous task
    params = kwargs["ti"].xcom_pull(
        key="params", task_ids="cluster_acteurs_config_validate"
    )

    # Boucle pour automatiser l'affichage des paramètres de champs
    # et la construction d'un set de tous les champs (pour requête SQL)
    fields = ["source_id", "acteur_type_id", "nom"]
    for key, value in params.items():
        if key.startswith("include_") or key.startswith("exclude_"):
            log.preview(key, value)
        if "fields" in key:
            fields.extend(value or [])
    fields = sorted(list(set(fields)))
    log.preview("Tous les champs reseignés", fields)

    df, query = cluster_acteurs_db_data_read_acteurs(
        model_class=DisplayedActeur,
        include_source_ids=params["include_source_ids"],
        include_acteur_type_ids=params["include_acteur_type_ids"],
        include_only_if_regex_matches_nom=params["include_only_if_regex_matches_nom"],
        include_if_all_fields_filled=params["include_if_all_fields_filled"] or [],
        exclude_if_any_field_filled=params["exclude_if_any_field_filled"] or [],
        extra_dataframe_fields=fields,
    )
    log.preview("requête SQL utilisée", query)
    log.preview("acteurs sélectionnés", df)
    log.preview("# acteurs par source_id", df.groupby("source_id").size())
    log.preview("# acteurs par acteur_type_id", df.groupby("acteur_type_id").size())

    if df.empty:
        raise ValueError("Aucun acteur trouvé avec les critères de sélection")

    kwargs["ti"].xcom_push(key="df", value=df)


def cluster_acteurs_db_data_read_acteurs_task(dag: DAG) -> PythonOperator:
    """La tâche Airflow qui ne fait que appeler le wrapper"""
    return PythonOperator(
        task_id="cluster_acteurs_db_data_read_acteurs",
        python_callable=cluster_acteurs_db_data_read_acteurs_wrapper,
        dag=dag,
    )
