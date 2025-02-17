import logging

from airflow import DAG
from airflow.exceptions import AirflowSkipException
from airflow.operators.python import PythonOperator
from cluster.config.model import ClusterConfig
from cluster.tasks.airflow_logic.task_ids import (
    TASK_CONFIG_CREATE,
    TASK_PARENTS_CHOOSE_DATA,
    TASK_SUGGESTIONS_DISPLAY,
    TASK_SUGGESTIONS_TO_DB,
)
from cluster.tasks.business_logic.cluster_acteurs_suggestions.to_db import (
    cluster_acteurs_suggestions_to_db,
)
from utils import logging_utils as log

logger = logging.getLogger(__name__)


def task_info_get():
    return f"""


    ============================================================
    Description de la tâche "{TASK_SUGGESTIONS_TO_DB}"
    ============================================================

    💡 quoi: écriture des suggestions en base de données

    🎯 pourquoi: pour que le métier puisse revoir ces suggestions
    et décider les approuver ou non

    🏗️ comment: on utilise les tables définies par l'app django
    data_management
    """


def cluster_acteurs_suggestions_to_db_wrapper(**kwargs) -> None:

    logger.info(task_info_get())

    config: ClusterConfig = kwargs["ti"].xcom_pull(
        key="config", task_ids=TASK_CONFIG_CREATE
    )
    df_clusters = kwargs["ti"].xcom_pull(key="df", task_ids=TASK_PARENTS_CHOOSE_DATA)
    suggestions = kwargs["ti"].xcom_pull(
        key="suggestions", task_ids=TASK_SUGGESTIONS_DISPLAY
    )

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
        identifiant_action=f"dag_id={kwargs['dag'].dag_id}",
        identifiant_execution=f"run_id={kwargs['run_id']}",
    )

    logging.info(log.banner_string("🏁 Résultat final de cette tâche"))
    logging.info(f"{len(suggestions)} suggestions de clusters écrites en base")


def cluster_acteurs_suggestions_to_db_task(dag: DAG) -> PythonOperator:
    return PythonOperator(
        task_id=TASK_SUGGESTIONS_TO_DB,
        python_callable=cluster_acteurs_suggestions_to_db_wrapper,
        dag=dag,
    )
