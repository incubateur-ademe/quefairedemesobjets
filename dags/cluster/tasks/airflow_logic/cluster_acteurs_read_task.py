import logging

from airflow import DAG
from airflow.exceptions import AirflowSkipException
from airflow.operators.python import PythonOperator
from cluster.config.model import ClusterConfig
from cluster.config.tasks import TASKS
from cluster.config.xcoms import XCOMS, xcom_pull
from cluster.tasks.business_logic.cluster_acteurs_read.for_clustering import (
    cluster_acteurs_read_for_clustering,
)
from utils import logging_utils as log

logger = logging.getLogger(__name__)


def task_info_get():
    return f"""


    ============================================================
    Description de la tâche "{TASKS.SELECTION}"
    ============================================================

    💡 quoi: va chercher en base de données les acteurs correspondants
        aux critères d'inclusion et d'exclusion du DAG
         - ces acteurs "candidats" ne seront pas forcément utilisés
         dans des clusters

    🎯 pourquoi: c'est la donnée de base dont on a besoin pour le clustering

    🏗️ comment: constructions/execution d'une requête SQL sur la base
        des critrères d'inclusion/exclusion
    """


def cluster_acteurs_read_wrapper(ti) -> None:
    logger.info(task_info_get())

    config: ClusterConfig = xcom_pull(ti, XCOMS.CONFIG)
    log.preview("Config reçue", config)

    df = cluster_acteurs_read_for_clustering(
        include_source_ids=config.include_source_ids,
        apply_include_sources_to_parents=config.apply_include_sources_to_parents,
        include_acteur_type_ids=config.include_acteur_type_ids,
        apply_include_acteur_types_to_parents=config.apply_include_acteur_types_to_parents,
        include_only_if_regex_matches_nom=config.include_only_if_regex_matches_nom,
        apply_include_only_if_regex_matches_nom_to_parents=(
            config.apply_include_only_if_regex_matches_nom_to_parents
        ),
        include_if_all_fields_filled=config.include_if_all_fields_filled,
        apply_include_if_all_fields_filled_to_parents=(
            config.apply_include_if_all_fields_filled_to_parents
        ),
        fields_protected=config.fields_protected,
        fields_transformed=config.fields_transformed,
    )

    if df.empty:
        raise AirflowSkipException("Aucun orphelin trouvé, on s'arrête là")

    logging.info(log.banner_string("🏁 Résultat final de cette tâche"))
    log.preview_df_as_markdown("acteurs sélectionnés", df)

    ti.xcom_push(key=XCOMS.DF_READ, value=df)


def cluster_acteurs_read_task(dag: DAG) -> PythonOperator:
    return PythonOperator(
        task_id=TASKS.SELECTION,
        python_callable=cluster_acteurs_read_wrapper,
        dag=dag,
    )
