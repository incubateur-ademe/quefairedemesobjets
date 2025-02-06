import logging

from airflow import DAG
from airflow.operators.python import PythonOperator
from compute_acteurs.tasks.business_logic import deduplicate_propositionservices
from utils import logging_utils as log

logger = logging.getLogger(__name__)


def deduplicate_propositionservices_task(dag: DAG) -> PythonOperator:
    return PythonOperator(
        task_id="deduplicate_propositionservices",
        python_callable=deduplicate_propositionservices_wrapper,
        dag=dag,
    )


def deduplicate_propositionservices_wrapper(**kwargs):
    df_children = kwargs["ti"].xcom_pull(task_ids="compute_acteur")["df_children"]
    dfs_ps = kwargs["ti"].xcom_pull(task_ids="compute_ps")
    df_propositionservice_merged = dfs_ps["df_propositionservice_merged"]
    df_propositionservice_sous_categories_merged = dfs_ps[
        "df_propositionservice_sous_categories_merged"
    ]

    log.preview("df_children", df_children)
    log.preview("df_propositionservice", df_propositionservice_merged)
    log.preview(
        "df_propositionservice_sous_categories",
        df_propositionservice_sous_categories_merged,
    )

    return deduplicate_propositionservices(
        df_children=df_children,
        df_ps=df_propositionservice_merged,
        df_ps_sscat=df_propositionservice_sous_categories_merged,
    )
