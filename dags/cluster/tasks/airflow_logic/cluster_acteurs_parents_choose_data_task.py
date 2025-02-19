import logging

import pandas as pd
from airflow import DAG
from airflow.operators.python import PythonOperator
from cluster.config.model import ClusterConfig
from cluster.tasks.airflow_logic.task_ids import (
    TASK_CONFIG_CREATE,
    TASK_PARENTS_CHOOSE_DATA,
    TASK_PARENTS_CHOOSE_NEW,
)
from cluster.tasks.business_logic.cluster_acteurs_parents_choose_data import (
    cluster_acteurs_parents_choose_data,
)
from utils import logging_utils as log

logger = logging.getLogger(__name__)


def task_info_get():
    return f"""


    ============================================================
    Description de la tâche "{TASK_PARENTS_CHOOSE_DATA}"
    ============================================================

    💡 quoi: sélectionne la donnée à assigner au parent

    🎯 pourquoi: pouvoir enrichir le parent à partir de la donnée
    des différents acteurs du cluster

    🏗️ comment: règles métier à définir
    """


def cluster_acteurs_parents_choose_data_wrapper(**kwargs) -> None:
    logger.info(task_info_get())

    # use xcom to get the params from the previous task
    config: ClusterConfig = kwargs["ti"].xcom_pull(
        key="config", task_ids=TASK_CONFIG_CREATE
    )
    df: pd.DataFrame = kwargs["ti"].xcom_pull(
        key="df", task_ids=TASK_PARENTS_CHOOSE_NEW
    )
    if not isinstance(df, pd.DataFrame) or df.empty:
        raise ValueError("df vide: on devrait pas être ici")

    log.preview("config reçue", config)
    log.preview("acteurs groupés", df)

    df = cluster_acteurs_parents_choose_data(
        df_clusters=df,
        fields_to_include=config.dedup_enrich_fields,
        exclude_source_ids=config.dedup_enrich_exclude_source_ids,
        prioritize_source_ids=config.dedup_enrich_priority_source_ids,
        keep_empty=config.dedup_enrich_keep_empty,
    )

    logging.info(log.banner_string("🏁 Résultat final de cette tâche"))
    log.preview_df_as_markdown("clusters avec data parent", df, groupby="cluster_id")

    kwargs["ti"].xcom_push(key="df", value=df)


def cluster_acteurs_parents_choose_data_task(dag: DAG) -> PythonOperator:
    return PythonOperator(
        task_id=TASK_PARENTS_CHOOSE_DATA,
        python_callable=cluster_acteurs_parents_choose_data_wrapper,
        dag=dag,
    )
