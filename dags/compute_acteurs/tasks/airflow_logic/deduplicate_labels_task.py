import logging

from airflow import DAG
from airflow.operators.python import PythonOperator
from compute_acteurs.tasks.business_logic import deduplicate_labels
from utils import logging_utils as log

logger = logging.getLogger(__name__)


def deduplicate_labels_task(dag: DAG) -> PythonOperator:
    return PythonOperator(
        task_id="deduplicate_labels",
        python_callable=deduplicate_labels_wrapper,
        dag=dag,
    )


def deduplicate_labels_wrapper(**kwargs):

    df_children = kwargs["ti"].xcom_pull(task_ids="apply_corrections_acteur")[
        "df_children"
    ]
    df_merge_labels = kwargs["ti"].xcom_pull(task_ids="merge_labels")

    log.preview("df_children", df_children)
    log.preview("df_merged_relationship", df_merge_labels)

    return deduplicate_labels(
        df_children=df_children,
        df_merge_labels=df_merge_labels,
    )
