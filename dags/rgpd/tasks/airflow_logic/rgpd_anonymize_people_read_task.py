"""Read data from DB needed for RGPD anonymization"""

import logging

from airflow import DAG
from airflow.exceptions import AirflowSkipException
from airflow.operators.python import PythonOperator
from rgpd.config import TASKS, XCOMS
from rgpd.tasks.business_logic.rgpd_anonymize_people_read import (
    rgpd_anonymize_people_read,
)

logger = logging.getLogger(__name__)


def task_info_get():
    return f"""
    ============================================================
    Description de la tâche "{TASKS.READ}"
    ============================================================
    💡 quoi: lecture des données de la base (QFDMO Acteurs
    et Unité Légales de l'Annuaire Entreprise)

    🎯 pourquoi: faire un pré-filtre sur les matches potentiels
    (pas récupérer les ~27M de lignes de la table AE)

    🏗️ comment: on récupère uniquement les matches SIREN avec
    des infos de noms/prénoms dans l'AE
    """


def rgpd_anonymize_people_read_wrapper(ti, params) -> None:
    logger.info(task_info_get())

    df = rgpd_anonymize_people_read(
        filter_comments_contain=params["filter_comments_contain"]
    )
    if df.empty:
        raise AirflowSkipException("Pas de données DB, on s'arrête là")

    ti.xcom_push(key=XCOMS.DF_READ, value=df)


def rgpd_anonymize_people_read_task(dag: DAG) -> PythonOperator:
    return PythonOperator(
        task_id=TASKS.READ,
        python_callable=rgpd_anonymize_people_read_wrapper,
        dag=dag,
    )
