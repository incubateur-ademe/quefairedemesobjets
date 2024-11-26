import logging

from airflow import DAG
from airflow.operators.python import PythonOperator
from shared.tasks.business_logic.write_data import write_data
from utils import logging_utils as log

logger = logging.getLogger(__name__)


def write_data_task(dag: DAG) -> PythonOperator:
    return PythonOperator(
        task_id="db_data_write",
        python_callable=write_data_wrapper,
        dag=dag,
    )


def write_data_wrapper(**kwargs) -> None:
    dag_name = kwargs["dag"].dag_display_name or kwargs["dag"].dag_id
    run_id = kwargs["run_id"]
    dfs = kwargs["ti"].xcom_pull(task_ids="db_data_prepare")
    metadata_actors = (
        kwargs["ti"]
        .xcom_pull(task_ids="propose_acteur_changes", key="return_value", default={})
        .get("metadata", {})
    )
    metadata_acteur_to_delete = (
        kwargs["ti"]
        .xcom_pull(task_ids="propose_acteur_to_delete", key="return_value", default={})
        .get("metadata", {})
    )
    metadata_pds = (
        kwargs["ti"]
        .xcom_pull(task_ids="propose_services", key="return_value", default={})
        .get("metadata", {})
    )

    log.preview("dag_name", dag_name)
    log.preview("run_id", run_id)
    log.preview("metadata_actors", metadata_actors)
    log.preview("metadata_acteur_to_delete", metadata_acteur_to_delete)
    log.preview("metadata_pds", metadata_pds)

    return write_data(
        dag_name=dag_name,
        run_id=run_id,
        dfs=dfs,
        metadata_actors=metadata_actors,
        metadata_acteur_to_delete=metadata_acteur_to_delete,
        metadata_pds=metadata_pds,
    )
