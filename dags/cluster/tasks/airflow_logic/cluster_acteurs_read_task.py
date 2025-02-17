import logging

from airflow import DAG
from airflow.exceptions import AirflowSkipException
from airflow.operators.python import PythonOperator
from cluster.config.model import ClusterConfig
from cluster.tasks.airflow_logic.task_ids import TASK_CONFIG_CREATE, TASK_SELECTION
from cluster.tasks.business_logic.cluster_acteurs_read.for_clustering import (
    cluster_acteurs_read_for_clustering,
)
from utils import logging_utils as log

logger = logging.getLogger(__name__)


def task_info_get():
    return f"""


    ============================================================
    Description de la tâche "{TASK_SELECTION}"
    ============================================================

    💡 quoi: va chercher en base de données les acteurs correspondants
        aux critères d'inclusion et d'exclusion du DAG
         - ces acteurs "candidats" ne seront pas forcément utilisés
         dans des clusters

    🎯 pourquoi: c'est la donnée de base dont on a besoin pour le clustering

    🏗️ comment: constructions/execution d'une requête SQL sur la base
        des critrères d'inclusion/exclusion
    """


def cluster_acteurs_read_wrapper(**kwargs) -> None:
    logger.info(task_info_get())

    config: ClusterConfig = kwargs["ti"].xcom_pull(
        key="config", task_ids=TASK_CONFIG_CREATE
    )
    log.preview("Config reçue", config)

    df = cluster_acteurs_read_for_clustering(
        include_source_ids=config.include_source_ids,
        include_acteur_type_ids=config.include_acteur_type_ids,
        include_only_if_regex_matches_nom=config.include_only_if_regex_matches_nom,
        include_if_all_fields_filled=config.include_if_all_fields_filled,
        exclude_if_any_field_filled=config.exclude_if_any_field_filled,
        include_parents_only_if_regex_matches_nom=config.include_parents_only_if_regex_matches_nom,
        fields_protected=config.fields_protected,
        fields_transformed=config.fields_transformed,
    )

    if df.empty:
        raise AirflowSkipException("Aucun orphelin trouvé pour le clustering")

    logging.info(log.banner_string("🏁 Résultat final de cette tâche"))
    log.preview_df_as_markdown("acteurs sélectionnés", df)

    kwargs["ti"].xcom_push(key="df", value=df)


def cluster_acteurs_read_task(dag: DAG) -> PythonOperator:
    return PythonOperator(
        task_id=TASK_SELECTION,
        python_callable=cluster_acteurs_read_wrapper,
        dag=dag,
    )
