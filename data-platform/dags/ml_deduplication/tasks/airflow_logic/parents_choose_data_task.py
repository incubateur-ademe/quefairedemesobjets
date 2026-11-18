"""Tâche Airflow de sélection de la donnée à assigner au parent (ML-déduplication)"""

import logging

import pandas as pd
from airflow.providers.standard.operators.python import PythonOperator
from cluster.tasks.airflow_logic.utils import parent_data_new_serialize
from cluster.tasks.business_logic.cluster_acteurs_parents_choose_data import (
    cluster_acteurs_parents_choose_data,
)
from ml_deduplication.config.models import MLDeduplicationConfig
from ml_deduplication.config.tasks import TASKS
from ml_deduplication.config.xcoms import XCOMS, xcom_pull, xcom_push
from utils import logging_utils as log

logger = logging.getLogger(__name__)


def task_info_get():
    return f"""


    ============================================================
    Description de la tâche "{TASKS.PARENTS_CHOOSE_DATA}"
    ============================================================

    💡 quoi: sélectionne la donnée à assigner au parent

    🎯 pourquoi: pouvoir enrichir le parent à partir de la donnée
        des différents acteurs du cluster

    🏗️ comment: règles métier à définir
    """


def ml_deduplication_parents_choose_data_wrapper(ti) -> None:
    logger.info(task_info_get())

    config: MLDeduplicationConfig = xcom_pull(ti, XCOMS.CONFIG)
    df: pd.DataFrame = xcom_pull(ti, XCOMS.DF_PARENTS_CHOOSE_NEW)

    if not isinstance(df, pd.DataFrame) or df.empty:
        raise ValueError("df vide: on devrait pas être ici")

    log.preview("config reçue", config)
    log.preview_dict_subsets(config.__dict__, key_pattern="dedup_enrich_")
    if "acteur_type_id" in df.columns:
        df["acteur_type_id"] = df["acteur_type_id"].astype("Int64")
    log.preview("acteurs groupés", df)
    log.preview("config.dedup_enrich_fields", config.dedup_enrich_fields)
    df = cluster_acteurs_parents_choose_data(
        df_clusters=df,
        fields_to_include=config.dedup_enrich_fields,
        exclude_source_ids=config.dedup_enrich_exclude_source_ids,
        prioritize_source_ids=config.dedup_enrich_priority_source_ids,
        keep_empty=config.dedup_enrich_keep_empty,
        keep_parent_data_by_default=config.dedup_enrich_keep_parent_data_by_default,
    )

    logger.info(log.banner_string("🏁 Résultat final de cette tâche"))
    log.preview_df_as_markdown("clusters avec data parent", df, groupby="cluster_id")

    # JSON-encode the dict column so it survives Parquet-based XCom transport
    xcom_push(ti, XCOMS.DF_PARENTS_CHOOSE_DATA, parent_data_new_serialize(df))


def ml_deduplication_parents_choose_data_task() -> PythonOperator:
    return PythonOperator(
        task_id=TASKS.PARENTS_CHOOSE_DATA,
        python_callable=ml_deduplication_parents_choose_data_wrapper,
    )
