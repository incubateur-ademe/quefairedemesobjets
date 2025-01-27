import logging

from airflow import DAG
from airflow.operators.python import PythonOperator
from cluster.tasks.business_logic.cluster_acteurs_suggestions_validate import (
    cluster_acteurs_suggestions_validate,
)
from utils import logging_utils as log

logger = logging.getLogger(__name__)


def task_info_get():
    return """


    ============================================================
    Description de la tâche "cluster_acteurs_suggestions_validate"
    ============================================================

    💡 quoi: validation des suggestions après l'affichage airflow mais
    avant et comme condition à l'écriture en base de données

    🎯 pourquoi: on tolère des suggestions potentiellement erronées
    au niveau de l'affichage airflow pour faciliter le debug, en revanche
    la validation est stricte et ne doit rien laisser passer au niveau de
    la DB (éviter les compute/bruit inutiles ET surtout éviter des approbations
    de suggestions malencontreuses qui viendraient créer le chaos dans
    les acteurs)

    🏗️ comment: règles de validations appliquées:
     - aucun acteur non-ACTIF
     - chaque cluster doit avoir au moins 2 acteurs
    """


def cluster_acteurs_suggestions_validate_wrapper(**kwargs) -> None:
    logger.info(task_info_get())

    df = kwargs["ti"].xcom_pull(
        key="df", task_ids="cluster_acteurs_suggestions_display"
    )

    log.preview("suggestions de clustering", df)

    cluster_acteurs_suggestions_validate(df)

    logging.info(log.banner_string("🏁 Résultat final de cette tâche"))
    logging.info(" - Validation des suggestions: succès ✅")
    logging.info(" - 0 modification de quoi que ce soit à ce stade (validation pure)")


def cluster_acteurs_suggestions_validate_task(dag: DAG) -> PythonOperator:
    return PythonOperator(
        task_id="cluster_acteurs_suggestions_validate",
        python_callable=cluster_acteurs_suggestions_validate_wrapper,
        dag=dag,
    )
