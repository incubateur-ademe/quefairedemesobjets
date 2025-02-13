import logging

from airflow import DAG
from airflow.exceptions import AirflowSkipException
from airflow.operators.python import PythonOperator
from cluster.tasks.airflow_logic.task_ids import TASK_PARENTS_CHOOSE_DATA

logger = logging.getLogger(__name__)


def task_info_get():
    return f"""


    ============================================================
    Description de la tâche "{TASK_PARENTS_CHOOSE_DATA}"
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
        task_id=TASK_PARENTS_CHOOSE_DATA,
        python_callable=cluster_acteurs_parents_choose_data_wrapper,
        dag=dag,
    )
