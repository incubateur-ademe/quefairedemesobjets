"""Match acteurs from QFDMO vs. AE based on people names"""

import logging

from airflow import DAG
from airflow.exceptions import AirflowSkipException
from airflow.operators.python import PythonOperator
from rgpd.config import COLS, TASKS, XCOMS
from rgpd.tasks.business_logic.rgpd_anonymize_people_match import (
    rgpd_anonymize_people_match,
)

logger = logging.getLogger(__name__)


def task_info_get():
    return f"""
    ============================================================
    Description de la tâche "{TASKS.MATCH_SCORE}"
    ============================================================
    💡 quoi: on cherche à déterminer quels acteurs QFDMO ont un
    nom qui correspond à des noms de personnes dans l'AE

    🎯 pourquoi: le but de ce DAG: pouvoir par la suite anonymiser

    🏗️ comment: normalisation puis matching python sur la base
    du ratio de mots dans le nom de l'acteur qui matchent avec des
    noms/prénoms de personnes dans l'AE
    """


def rgpd_anonymize_people_match_wrapper(ti, params) -> None:
    logger.info(task_info_get())

    df = rgpd_anonymize_people_match(
        df=ti.xcom_pull(key=XCOMS.DF_READ),
        match_threshold=params[COLS.MATCH_THRESHOLD],
    )
    if df.empty:
        raise AirflowSkipException("Pas de matches, on s'arrête là")

    ti.xcom_push(key=XCOMS.DF_MATCH, value=df)


def rgpd_anonymize_people_match_task(dag: DAG) -> PythonOperator:
    return PythonOperator(
        task_id=TASKS.MATCH_SCORE,
        python_callable=rgpd_anonymize_people_match_wrapper,
        dag=dag,
    )
