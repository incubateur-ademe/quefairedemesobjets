import logging

from airflow import DAG
from airflow.operators.python import PythonOperator
from sources.tasks.business_logic.propose_labels import propose_labels
from utils import logging_utils as log

logger = logging.getLogger(__name__)


def propose_labels_task(dag: DAG) -> PythonOperator:
    return PythonOperator(
        task_id="propose_labels",
        python_callable=propose_labels_wrapper,
        dag=dag,
    )


def propose_labels_wrapper(**kwargs):
    labelqualite_id_by_code = kwargs["ti"].xcom_pull(task_ids="db_read_labelqualite")
    acteurtype_id_by_code = kwargs["ti"].xcom_pull(task_ids="db_read_acteurtype")
    df_actors = kwargs["ti"].xcom_pull(task_ids="propose_acteur_changes")["df"]

    log.preview(df_actors, "df_actors")
    log.preview(labelqualite_id_by_code, "labelqualite_id_by_code")
    log.preview(acteurtype_id_by_code, "acteurtype_id_by_code")

    return propose_labels(
        df_acteur=df_actors,
        labelqualite_id_by_code=labelqualite_id_by_code,
    )
