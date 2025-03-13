"""Match acteurs from QFDMO vs. AE based on people names"""

import logging

from airflow import DAG
from airflow.exceptions import AirflowSkipException
from airflow.operators.python import PythonOperator
from rgpd.config import COLS, TASKS, XCOMS
from rgpd.tasks.business_logic.rgpd_anonymize_people_suggest import (
    rgpd_anonymize_people_suggest,
)

logger = logging.getLogger(__name__)


def task_info_get():
    return f"""
    ============================================================
    Description de la tâche "{TASKS.SUGGEST}"
    ============================================================
    💡 quoi: on cherche à déterminer quels acteurs QFDMO ont un
    nom qui correspond à des noms de personnes dans l'AE

    🎯 pourquoi: le but de ce DAG: pouvoir par la suite anonymiser

    🏗️ comment: normalisation puis suggesting python sur la base
    du ratio de mots dans le nom de l'acteur qui suggestent avec des
    noms/prénoms de personnes dans l'AE
    """


def rgpd_anonymize_people_suggest_wrapper(ti, params, dag, run_id) -> None:
    logger.info(task_info_get())

    rgpd_anonymize_people_suggest(
        df=ti.xcom_pull(key=XCOMS.DF_MATCH),
        identifiant_action=dag.dag_id,
        identifiant_execution=run_id,
        dry_run=params[COLS.DRY_RUN],
    )
    # Flagging as skipped at the end to help read status in Airflow UI
    if params[COLS.DRY_RUN]:
        raise AirflowSkipException("Pas de données DB, on s'arrête là")


def rgpd_anonymize_people_suggest_task(dag: DAG) -> PythonOperator:
    return PythonOperator(
        task_id=TASKS.SUGGEST,
        python_callable=rgpd_anonymize_people_suggest_wrapper,
        dag=dag,
    )
