import logging

from airflow import DAG
from airflow.operators.python import PythonOperator
from sources.tasks.business_logic.propose_services import propose_services
from utils import logging_utils as log

logger = logging.getLogger(__name__)


def propose_services_task(dag: DAG) -> PythonOperator:
    return PythonOperator(
        task_id="propose_services",
        python_callable=propose_services_wrapper,
        dag=dag,
    )


def propose_services_wrapper(**kwargs) -> dict:
    df = kwargs["ti"].xcom_pull(task_ids="propose_acteur_changes")["df"]
    data_dict = kwargs["ti"].xcom_pull(task_ids="db_read_propositions_max_id")
    displayedpropositionservice_max_id = data_dict["displayedpropositionservice_max_id"]
    actions_id_by_code = kwargs["ti"].xcom_pull(task_ids="db_read_action")

    log.preview("df depuis propose_acteur_changes", df)
    log.preview(
        "displayedpropositionservice_max_id", displayedpropositionservice_max_id
    )
    log.preview("actions_id_by_code", actions_id_by_code)

    return propose_services(
        df=df,
        displayedpropositionservice_max_id=displayedpropositionservice_max_id,
        actions_id_by_code=actions_id_by_code,
    )
