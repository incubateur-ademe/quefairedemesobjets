import logging

from airflow import DAG
from airflow.providers.standard.operators.python import PythonOperator
from airflow.sdk.exceptions import AirflowSkipException
from cluster.config.models import ClusterConfig
from cluster.config.tasks import TASKS
from cluster.config.xcoms import XCOMS, xcom_pull
from cluster.tasks.business_logic.cluster_acteurs_config_create import (
    cluster_acteurs_config_create,
)
from cluster.tasks.business_logic.cluster_acteurs_suggestions.to_db import (
    cluster_acteurs_suggestions_to_db,
)
from utils import logging_utils as log

logger = logging.getLogger(__name__)


def task_info_get():
    return f"""


    ============================================================
    Description de la tâche "{TASKS.SUGGESTIONS_TO_DB}"
    ============================================================

    💡 quoi: écriture des suggestions en base de données

    🎯 pourquoi: l'objectif final du DAG

    🏗️ comment: suggestions préparées par la tâche précédente écrite
    en DB via modèles Django
    """


def cluster_acteurs_suggestions_to_db_wrapper(ti, params, dag, run_id) -> None:

    logger.info(task_info_get())

    config: ClusterConfig = cluster_acteurs_config_create(params)
    df_clusters = xcom_pull(ti, XCOMS.DF_PARENTS_CHOOSE_DATA)
    suggestions = xcom_pull(ti, XCOMS.SUGGESTIONS_WORKING)

    log.preview("config", config)
    log.preview("df_clusters", df_clusters)
    log.preview("suggestions", suggestions)

    # "is not False" more robust than "is true" due to potential None
    if config.dry_run is not False:
        msg = log.banner_string(f"Dry run ={config.dry_run}, on n'écrit pas en DB")
        raise AirflowSkipException(msg)

    cluster_acteurs_suggestions_to_db(
        df_clusters=df_clusters,
        suggestions=suggestions,
        identifiant_action=dag.dag_display_name,
        identifiant_execution=run_id,
        # Rest assured: we are no longer clustering, but
        # we use cluster config to generate useful context
        # data for the Django Admin UI
        cluster_fields_exact=config.cluster_fields_exact,
        cluster_fields_fuzzy=config.cluster_fields_fuzzy,
    )

    logger.info(log.banner_string("🏁 Résultat final de cette tâche"))
    logger.info(f"{len(suggestions)} suggestions de clusters écrites en base")


def cluster_acteurs_suggestions_to_db_task(dag: DAG) -> PythonOperator:
    return PythonOperator(
        task_id=TASKS.SUGGESTIONS_TO_DB,
        python_callable=cluster_acteurs_suggestions_to_db_wrapper,
        dag=dag,
    )
