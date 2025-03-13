"""Read data from DB needed for enrich anonymization"""

import logging

from airflow import DAG
from airflow.exceptions import AirflowSkipException
from airflow.operators.python import PythonOperator
from enrich.config import TASKS, XCOMS
from enrich.tasks.business_logic.close_acteurs_via_ae_read import (
    close_acteurs_via_ae_read,
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


def close_acteurs_via_ae_read_wrapper(ti, params) -> None:
    logger.info(task_info_get())

    df = close_acteurs_via_ae_read()
    if df.empty:
        raise AirflowSkipException("Pas de données DB, on s'arrête là")

    ti.xcom_push(key=XCOMS.DF_READ, value=df)


def close_acteurs_via_ae_read_task(dag: DAG) -> PythonOperator:
    return PythonOperator(
        task_id=TASKS.READ,
        python_callable=close_acteurs_via_ae_read_wrapper,
        dag=dag,
    )
