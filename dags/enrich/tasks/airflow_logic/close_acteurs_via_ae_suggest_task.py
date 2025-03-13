"""Match acteurs from QFDMO vs. AE based on people names"""

import logging

from airflow import DAG
from airflow.exceptions import AirflowSkipException
from airflow.operators.python import PythonOperator
from enrich.config import COLS, TASKS, XCOMS
from enrich.tasks.business_logic.close_acteurs_via_ae_suggest import (
    close_acteurs_via_ae_suggest,
)

logger = logging.getLogger(__name__)


def task_info_get():
    return f"""
    ============================================================
    Description de la tâche "{TASKS.SUGGEST}"
    ============================================================
    💡 quoi: génère les suggestions

    🎯 pourquoi: permettre au métier d'approuver/rejeter

    🏗️ comment: préparation des suggestions puis écriture DB
    si dry_run=False
    """


def close_acteurs_via_ae_suggest_wrapper(ti, params, dag, run_id) -> None:
    logger.info(task_info_get())

    close_acteurs_via_ae_suggest(
        df=ti.xcom_pull(key=XCOMS.DF_READ),
        identifiant_action=dag.dag_id,
        identifiant_execution=run_id,
        dry_run=params[COLS.DRY_RUN],
    )
    # Flagging as skipped at the end to help read status in Airflow UI
    if params[COLS.DRY_RUN]:
        raise AirflowSkipException("Pas de données DB, on s'arrête là")


def close_acteurs_via_ae_suggest_task(dag: DAG) -> PythonOperator:
    return PythonOperator(
        task_id=TASKS.SUGGEST,
        python_callable=close_acteurs_via_ae_suggest_wrapper,
        dag=dag,
    )
