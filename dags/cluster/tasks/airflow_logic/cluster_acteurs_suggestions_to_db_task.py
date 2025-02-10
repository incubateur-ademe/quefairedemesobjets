import logging

import pandas as pd
from airflow import DAG
from airflow.exceptions import AirflowSkipException
from airflow.operators.python import PythonOperator
from cluster.config.model import ClusterConfig
from cluster.tasks.airflow_logic.task_ids import (
    TASK_CONFIG_CREATE,
    TASK_SUGGESTIONS_DISPLAY,
    TASK_SUGGESTIONS_TO_DB,
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
    from cluster.tasks.business_logic import cluster_acteurs_suggestions_to_db

    logger.info(task_info_get())

    # use xcom to get the params from the previous task
    config: ClusterConfig = kwargs["ti"].xcom_pull(
        key="config", task_ids=TASK_CONFIG_CREATE
    )
    df: pd.DataFrame = kwargs["ti"].xcom_pull(
        key="df", task_ids=TASK_SUGGESTIONS_DISPLAY
    )
    dag_id = kwargs["dag"].dag_id
    run_id = kwargs["run_id"]

    log.preview("DAG ID", dag_id)
    log.preview("Run ID", run_id)
    log.preview("config reçue", config)
    log.preview("suggestions de clustering", df)

    # "is not False" est plus robuste que "is True" car on peut avoir None
    # par erreur dans la config et on ne veut pas prendre celoa pour
    # un signal de modifier la DB
    if config.dry_run is not False:
        raise AirflowSkipException(
            log.banner_string(f"Dry run ={config.dry_run}, on passe")
        )

    cluster_acteurs_suggestions_to_db(
        df_clusters=df,
        identifiant_action=f"dag_id={dag_id}",
        identifiant_execution=f"run_id={run_id}",
    )

    logging.info(log.banner_string("🏁 Résultat final de cette tâche"))
    logging.info(
        f"{df["cluster_id"].nunique()} suggestions de clusters écrites en base"
    )


def cluster_acteurs_suggestions_to_db_task(dag: DAG) -> PythonOperator:
    """La tâche Airflow qui ne fait que appeler le wrapper"""
    return PythonOperator(
        task_id=TASK_SUGGESTIONS_TO_DB,
        python_callable=cluster_acteurs_suggestions_to_db_wrapper,
        dag=dag,
    )
