import logging

from airflow import DAG
from airflow.operators.python import PythonOperator
from sources.tasks.business_logic.propose_ps import propose_ps
from utils import logging_utils as log

logger = logging.getLogger(__name__)


def propose_ps_task(dag: DAG) -> PythonOperator:
    return PythonOperator(
        task_id="propose_ps",
        python_callable=propose_ps_wrapper,
        dag=dag,
    )


def propose_ps_wrapper(**kwargs) -> dict:
    df = kwargs["ti"].xcom_pull(task_ids="propose_acteur_changes")["df"]
    data_dict = kwargs["ti"].xcom_pull(task_ids="db_read_ps_max_id")
    dps_max_id = data_dict["dps_max_id"]
    actions_id_by_code = kwargs["ti"].xcom_pull(task_ids="db_read_action")

    log.preview("df depuis propose_acteur_changes", df)
    log.preview("dps_max_id", dps_max_id)
    log.preview("actions_id_by_code", actions_id_by_code)

    return propose_ps(
        df=df,
        dps_max_id=dps_max_id,
        actions_id_by_code=actions_id_by_code,
    )
