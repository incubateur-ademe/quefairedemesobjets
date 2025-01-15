import logging

import pandas as pd
from airflow import DAG
from airflow.exceptions import AirflowSkipException
from airflow.operators.python import PythonOperator
from utils import logging_utils as log

logger = logging.getLogger(__name__)


def task_info_get():
    return """


    ============================================================
    Description de la tâche "cluster_acteurs_db_data_write_suggestions"
    ============================================================

    💡 quoi: écriture des suggestions en base de données

    🎯 pourquoi: pour que le métier puisse revoir ces suggestions
    et décider les approuver ou non

    🏗️ comment: on utilise les tables définies par l'app django
    data_management
    """


def cluster_acteurs_db_data_write_suggestions_wrapper(**kwargs) -> None:
    logger.info(task_info_get())

    # use xcom to get the params from the previous task
    params = kwargs["ti"].xcom_pull(
        key="params", task_ids="cluster_acteurs_config_validate"
    )
    df: pd.DataFrame = kwargs["ti"].xcom_pull(
        key="df", task_ids="cluster_acteurs_suggestions"
    )

    log.preview("paramètres reçus", params)
    log.preview("suggestions de clustering", df)

    if params["dry_run"]:
        raise AirflowSkipException(
            log.banner_string("Dry run activé, suggestions pas écrites en base")
        )

    raise NotImplementedError(
        "Ecriture des suggestions en DB pas implémentée pour le moment"
    )


def cluster_acteurs_db_data_write_suggestions_task(dag: DAG) -> PythonOperator:
    """La tâche Airflow qui ne fait que appeler le wrapper"""
    return PythonOperator(
        task_id="cluster_acteurs_db_data_write_suggestions",
        python_callable=cluster_acteurs_db_data_write_suggestions_wrapper,
        dag=dag,
    )
