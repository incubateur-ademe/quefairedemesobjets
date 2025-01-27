import logging

from airflow import DAG
from airflow.operators.python import PythonOperator
from cluster.config.model import ClusterConfig
from cluster.tasks.business_logic.cluster_acteurs_df_sort import cluster_acteurs_df_sort
from cluster.tasks.business_logic.cluster_acteurs_selection_from_db import (
    cluster_acteurs_selection_from_db,
)
from utils import logging_utils as log
from utils.django import django_setup_full

django_setup_full()

from qfdmo.models import DisplayedActeur  # noqa: E402

logger = logging.getLogger(__name__)


def task_info_get():
    return """


    ============================================================
    Description de la tâche "cluster_acteurs_selection_from_db"
    ============================================================

    💡 quoi: va chercher en base de données les acteurs correspondants
        aux critères d'inclusion et d'exclusion du DAG
         - ces acteurs "candidats" ne seront pas forcément utilisés
         dans des clusters

    🎯 pourquoi: c'est la donnée de base dont on a besoin pour le clustering

    🏗️ comment: constructions/execution d'une requête SQL sur la base
        des critrères d'inclusion/exclusion
    """


def cluster_acteurs_selection_from_db_wrapper(**kwargs) -> None:
    logger.info(task_info_get())

    config: ClusterConfig = kwargs["ti"].xcom_pull(
        key="config", task_ids="cluster_acteurs_config_create"
    )
    log.preview("Config reçue", config)

    df, query = cluster_acteurs_selection_from_db(
        model_class=DisplayedActeur,
        include_source_ids=config.include_source_ids,
        include_acteur_type_ids=config.include_acteur_type_ids,
        include_only_if_regex_matches_nom=config.include_only_if_regex_matches_nom,
        include_if_all_fields_filled=config.include_if_all_fields_filled,
        exclude_if_any_field_filled=config.exclude_if_any_field_filled,
        extra_dataframe_fields=config.fields_used,
    )
    log.preview("requête SQL utilisée", query)
    log.preview("acteurs sélectionnés", df)
    log.preview("# acteurs par source_id", df.groupby("source_id").size())
    log.preview("# acteurs par acteur_type_id", df.groupby("acteur_type_id").size())

    if df.empty:
        raise ValueError("Aucun acteur trouvé avec les critères de sélection")

    logging.info(log.banner_string("🏁 Résultat final de cette tâche"))
    df = cluster_acteurs_df_sort(df)
    log.preview_df_as_markdown("acteurs sélectionnés", df)

    kwargs["ti"].xcom_push(key="df", value=df)


def cluster_acteurs_selection_from_db_task(dag: DAG) -> PythonOperator:
    """La tâche Airflow qui ne fait que appeler le wrapper"""
    return PythonOperator(
        task_id="cluster_acteurs_selection_from_db",
        python_callable=cluster_acteurs_selection_from_db_wrapper,
        dag=dag,
    )
