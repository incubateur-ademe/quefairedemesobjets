import logging

from airflow import DAG
from airflow.operators.python import PythonOperator
from cluster.tasks.airflow_logic.task_ids import TASK_SUGGESTIONS_DISPLAY

logger = logging.getLogger(__name__)


def task_info_get():
    return f"""


    ============================================================
    Description de la tâche "{TASK_SUGGESTIONS_DISPLAY}"
    ============================================================

    💡 quoi: affichage de l'état final des suggestions avant
    écriture en base

    🎯 pourquoi: avoir une vue d'ensemble au niveau airflow:
     - si on utilise le dry_un avant écriture
     - si quelque se passe mal au niveau de l'écriture en base

    🏗️ comment: pas de nouvelle données générées ici, on reprends
    juste les données des tâches précédentes qu'on essaye d'afficher
    de manière lisible
    """


def cluster_acteurs_suggestions_display_wrapper(**kwargs) -> None:
    logger.info(task_info_get())


def cluster_acteurs_suggestions_display_task(dag: DAG) -> PythonOperator:
    """La tâche Airflow qui ne fait que appeler le wrapper"""
    return PythonOperator(
        task_id=TASK_SUGGESTIONS_DISPLAY,
        python_callable=cluster_acteurs_suggestions_display_wrapper,
        dag=dag,
    )
