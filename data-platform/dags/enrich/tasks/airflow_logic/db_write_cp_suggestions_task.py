"""Generic task to create configuration"""

import logging

from airflow import DAG
from airflow.providers.standard.operators.python import PythonOperator
from enrich.config.tasks import TASKS
from enrich.config.xcoms import XCOMS, xcom_pull
from enrich.tasks.business_logic.db_write_cp_suggestions import db_write_cp_suggestions

logger = logging.getLogger(__name__)


def task_info_get():
    return f"""
    ============================================================
    Description de la tâche "{TASKS.DB_WRITE_CP_SUGGESTIONS}"
    ============================================================
    💡 quoi: écriture des suggestions de modifications de codes postaux

    🎯 pourquoi: suggérer des modifications de codes postaux

    🏗️ comment: on écrit les suggestions de modifications de codes postaux dasn la table
    des suggestions
    """


def db_write_cp_suggestions_wrapper(ti, dag, params) -> None:
    logger.info(task_info_get())

    normalized_acteur_cp = xcom_pull(ti, XCOMS.NORMALIZED_ACTEUR_CP)
    normalized_revision_acteur_cp = xcom_pull(ti, XCOMS.NORMALIZED_REVISION_ACTEUR_CP)

    db_write_cp_suggestions(
        df_acteur_cp=normalized_acteur_cp,
        df_revision_acteur_cp=normalized_revision_acteur_cp,
        identifiant_action=dag.dag_id,
        dry_run=False,
    )


def db_write_cp_suggestions_task(dag: DAG) -> PythonOperator:
    return PythonOperator(
        task_id=TASKS.DB_WRITE_CP_SUGGESTIONS,
        python_callable=db_write_cp_suggestions_wrapper,
        dag=dag,
        doc_md="📖 **Création de la config**",
    )
