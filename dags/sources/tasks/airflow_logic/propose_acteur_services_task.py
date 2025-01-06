import logging

from airflow import DAG
from airflow.operators.python import PythonOperator
from sources.tasks.business_logic.propose_acteur_services import propose_acteur_services
from utils import logging_utils as log

logger = logging.getLogger(__name__)


def propose_acteur_services_task(dag: DAG) -> PythonOperator:
    return PythonOperator(
        task_id="propose_acteur_services",
        python_callable=propose_acteur_services_wrapper,
        dag=dag,
    )


def propose_acteur_services_wrapper(**kwargs):
    acteurservice_id_by_code = kwargs["ti"].xcom_pull(task_ids="db_read_acteurservice")
    df_acteur = kwargs["ti"].xcom_pull(task_ids="propose_acteur_changes")["df"]

    log.preview(df_acteur, "df_actors")
    log.preview(acteurservice_id_by_code, "acteurservice_id_by_code")

    return propose_acteur_services(
        df_acteur=df_acteur,
        acteurservice_id_by_code=acteurservice_id_by_code,
    )
