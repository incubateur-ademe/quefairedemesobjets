import logging

from airflow import DAG
from airflow.operators.python import PythonOperator
from compute_acteurs.tasks.business_logic import compute_parent_ps
from utils import logging_utils as log

logger = logging.getLogger(__name__)


def compute_parent_ps_task(dag: DAG) -> PythonOperator:
    return PythonOperator(
        task_id="deduplicate_ps",
        python_callable=compute_parent_ps_wrapper,
        dag=dag,
    )


def compute_parent_ps_wrapper(**kwargs):
    df_children = kwargs["ti"].xcom_pull(task_ids="apply_corrections_acteur")[
        "df_children"
    ]
    dfs_ps = kwargs["ti"].xcom_pull(task_ids="compute_ps")
    df_ps_merged = dfs_ps["df_ps_merged"]
    df_ps_sscat_merged = dfs_ps["df_ps_sscat_merged"]

    log.preview("df_children", df_children)
    log.preview("df_ps", df_ps_merged)
    log.preview(
        "df_ps_sscat",
        df_ps_sscat_merged,
    )

    return compute_parent_ps(
        df_children=df_children,
        df_ps=df_ps_merged,
        df_ps_sscat=df_ps_sscat_merged,
    )
