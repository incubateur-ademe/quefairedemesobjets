import logging

from airflow import DAG
from airflow.providers.standard.operators.python import PythonOperator
from enrich.config.tasks import TASKS
from enrich.config.xcoms import XCOMS
from enrich.tasks.business_logic.normalize_acteur_cp import normalize_acteur_cp
from utils import logging_utils as log

logger = logging.getLogger(__name__)


def task_info_get():
    return f"""
    ============================================================
    Description de la tâche "{TASKS.NORMALIZE_ACTEUR_CP}"
    ============================================================
    💡 quoi: normalisation des codes postaux des acteurs

    🎯 pourquoi: pour corriger les codes postaux non conformes

    🏗️ comment: on s'assure que les codes postaux sont sur 5 caractères digitaux
    """


def normalize_acteur_cp_wrapper(ti, dag, params) -> None:
    logger.info(task_info_get())

    db_acteur_cp = ti.xcom_pull(
        key=XCOMS.DB_READ_ACTEUR_CP, task_ids=TASKS.DB_READ_ACTEUR_CP
    )
    db_revision_acteur_cp = ti.xcom_pull(
        key=XCOMS.DB_READ_REVISION_ACTEUR_CP, task_ids=TASKS.DB_READ_ACTEUR_CP
    )

    normalized_acteur_cp = normalize_acteur_cp(db_acteur_cp)
    normalized_revision_acteur_cp = normalize_acteur_cp(db_revision_acteur_cp)
    log.preview_df_as_markdown(
        "acteurs avec des codes postaux normalisés", normalized_acteur_cp
    )
    log.preview_df_as_markdown(
        "revision acteurs avec des codes postaux normalisés",
        normalized_revision_acteur_cp,
    )

    ti.xcom_push(key=XCOMS.NORMALIZED_ACTEUR_CP, value=normalized_acteur_cp)
    ti.xcom_push(
        key=XCOMS.NORMALIZED_REVISION_ACTEUR_CP, value=normalized_revision_acteur_cp
    )


def normalize_acteur_cp_task(dag: DAG) -> PythonOperator:
    return PythonOperator(
        task_id=TASKS.NORMALIZE_ACTEUR_CP,
        python_callable=normalize_acteur_cp_wrapper,
        dag=dag,
        doc_md="📖 **Normalisation des codes postaux des acteurs et leur révision**",
    )
