import logging

from airflow import DAG
from airflow.providers.standard.operators.python import PythonOperator
from cluster.config.tasks import TASKS
from cluster.config.xcoms import XCOMS, xcom_pull
from cluster.tasks.business_logic.cluster_acteurs_clusters_validate import (
    cluster_acteurs_clusters_validate,
)
from utils import logging_utils as log

logger = logging.getLogger(__name__)


def task_info_get():
    return f"""


    ============================================================
    Description de la tâche "{TASKS.CLUSTERS_VALIDATE}"
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


def cluster_acteurs_clusters_validate_wrapper(ti) -> None:
    logger.info(task_info_get())

    df = xcom_pull(ti, XCOMS.DF_CLUSTERS_PREPARE)

    log.preview("acteurs clusterisés", df)

    cluster_acteurs_clusters_validate(df)

    logger.info(log.banner_string("🏁 Résultat final de cette tâche"))
    logger.info(" - Validation des suggestions: succès ✅")
    logger.info(" - 0 modification de quoi que ce soit à ce stade (validation pure)")


def cluster_acteurs_clusters_validate_task(dag: DAG) -> PythonOperator:
    return PythonOperator(
        task_id=TASKS.CLUSTERS_VALIDATE,
        python_callable=cluster_acteurs_clusters_validate_wrapper,
        dag=dag,
    )
