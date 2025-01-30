import logging

from airflow import DAG
from airflow.operators.python import PythonOperator

logger = logging.getLogger(__name__)


def task_info_get():
    return """


    ============================================================
    Description de la tâche "cluster_acteurs_suggestions_display"
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
        task_id="cluster_acteurs_suggestions_display",
        python_callable=cluster_acteurs_suggestions_display_wrapper,
        dag=dag,
    )
