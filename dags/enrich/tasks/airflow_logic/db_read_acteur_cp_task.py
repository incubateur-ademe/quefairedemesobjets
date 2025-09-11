"""Generic task to create configuration"""

import logging

from airflow import DAG
from airflow.operators.python import PythonOperator
from enrich.config.tasks import TASKS
from enrich.config.xcoms import XCOMS
from enrich.tasks.business_logic.db_read_acteur_cp import (
    db_read_acteur_cp,
    db_read_revision_acteur_cp,
)
from utils import logging_utils as log

logger = logging.getLogger(__name__)


def task_info_get():
    return f"""
    ============================================================
    Description de la tâche "{TASKS.DB_READ_ACTEUR_CP}"
    ============================================================
    💡 quoi: lecture des acteurs avec des codes postaux non conformes

    🎯 pourquoi: pour pouvoir les normaliser

    🏗️ comment: on va chercher les acteurs avec des codes postaux non conformes
    """


def db_read_acteur_cp_wrapper(ti, dag, params) -> None:
    logger.info(task_info_get())

    db_acteur_cp = db_read_acteur_cp()
    db_revision_acteur_cp = db_read_revision_acteur_cp()

    log.preview_df_as_markdown(
        "acteurs avec des codes postaux non conformes", db_acteur_cp
    )
    log.preview_df_as_markdown(
        "revision acteurs avec des codes postaux non conformes", db_revision_acteur_cp
    )

    ti.xcom_push(key=XCOMS.DB_READ_ACTEUR_CP, value=db_acteur_cp)
    ti.xcom_push(key=XCOMS.DB_READ_REVISION_ACTEUR_CP, value=db_revision_acteur_cp)


def db_read_acteur_cp_task(dag: DAG) -> PythonOperator:
    return PythonOperator(
        task_id=TASKS.DB_READ_ACTEUR_CP,
        python_callable=db_read_acteur_cp_wrapper,
        dag=dag,
        doc_md="📖 **Lecture des acteurs avec des codes postaux non conformes**",
    )
