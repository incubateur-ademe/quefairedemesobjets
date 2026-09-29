"""Tâche Airflow d'écriture des suggestions en base (ML-déduplication)"""

import logging

from airflow.providers.standard.operators.python import PythonOperator
from airflow.sdk.exceptions import AirflowSkipException
from cluster.tasks.airflow_logic.utils import parent_data_new_deserialize
from cluster.tasks.business_logic.cluster_acteurs_suggestions.to_db import (
    cluster_acteurs_suggestions_to_db,
)
from ml_deduplication.config.constants import DAG_DISPLAY_NAME
from ml_deduplication.config.models import MLDeduplicationConfig
from ml_deduplication.config.tasks import TASKS
from ml_deduplication.config.xcoms import XCOMS, xcom_pull
from utils import logging_utils as log

logger = logging.getLogger(__name__)


def task_info_get():
    return f"""


    ============================================================
    Description de la tâche "{TASKS.SUGGESTIONS_TO_DB}"
    ============================================================

    💡 quoi: écriture des suggestions en base de données

    🎯 pourquoi: l'objectif final du DAG

    🏗️ comment: suggestions préparées par la tâche précédente écrite
    en DB via modèles Django
    """


def ml_deduplication_suggestions_to_db_wrapper(ti) -> None:
    logger.info(task_info_get())

    config: MLDeduplicationConfig = xcom_pull(ti, XCOMS.CONFIG)
    run_id: str = xcom_pull(ti, XCOMS.RUN_ID)
    df_clusters = xcom_pull(ti, XCOMS.DF_PARENTS_CHOOSE_DATA)
    df_clusters = parent_data_new_deserialize(df_clusters)
    suggestions = xcom_pull(ti, XCOMS.SUGGESTIONS_WORKING)

    log.preview("config", config)
    log.preview("df_clusters", df_clusters)
    log.preview("suggestions", suggestions)

    # "is not False" more robust than "is true" due to potential None
    if config.dry_run is not False:
        msg = log.banner_string(f"Dry run ={config.dry_run}, on n'écrit pas en DB")
        raise AirflowSkipException(msg)

    cluster_acteurs_suggestions_to_db(
        df_clusters=df_clusters,
        suggestions=suggestions,
        identifiant_action=DAG_DISPLAY_NAME,
        identifiant_execution=run_id,
        # The ML clustering is done by the inference image, so we have no
        # exact/fuzzy fields.
        cluster_fields_exact=[],
        cluster_fields_fuzzy=[],
    )

    logger.info(log.banner_string("🏁 Résultat final de cette tâche"))
    logger.info(f"{len(suggestions)} suggestions de clusters écrites en base")


def ml_deduplication_suggestions_to_db_task() -> PythonOperator:
    return PythonOperator(
        task_id=TASKS.SUGGESTIONS_TO_DB,
        python_callable=ml_deduplication_suggestions_to_db_wrapper,
    )
