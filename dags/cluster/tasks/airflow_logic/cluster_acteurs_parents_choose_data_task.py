import logging

from airflow import DAG
from airflow.exceptions import AirflowSkipException
from airflow.operators.python import PythonOperator

logger = logging.getLogger(__name__)


def task_info_get():
    return """


    ============================================================
    Description de la tâche "cluster_acteurs_parents_choose_data"
    ============================================================

    💡 quoi: sélectionne la donnée à assigner au parent

    🎯 pourquoi: pouvoir enrichir le parent à partir de la donnée
    des différents acteurs du cluster

    🏗️ comment: règles métier à définir
    """


def cluster_acteurs_parents_choose_data_wrapper(**kwargs) -> None:
    logger.info(task_info_get())

    raise AirflowSkipException("Tâche pas encore implémentée")


def cluster_acteurs_parents_choose_data_task(dag: DAG) -> PythonOperator:
    """La tâche Airflow qui ne fait que appeler le wrapper"""
    return PythonOperator(
        task_id="cluster_acteurs_parents_choose_data",
        python_callable=cluster_acteurs_parents_choose_data_wrapper,
        dag=dag,
    )
