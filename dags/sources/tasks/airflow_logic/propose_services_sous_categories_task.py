import logging

from airflow import DAG
from airflow.operators.python import PythonOperator
from sources.tasks.business_logic.propose_services_sous_categories import (
    propose_services_sous_categories,
)
from utils import logging_utils as log

logger = logging.getLogger(__name__)


def propose_services_sous_categories_task(dag: DAG) -> PythonOperator:
    return PythonOperator(
        task_id="propose_services_sous_categories",
        python_callable=propose_services_sous_categories_wrapper,
        dag=dag,
    )


def propose_services_sous_categories_wrapper(**kwargs):
    df_ps = kwargs["ti"].xcom_pull(task_ids="propose_services")["df"]
    souscats_id_by_code = kwargs["ti"].xcom_pull(task_ids="db_read_souscategorieobjet")

    log.preview("df_ps", df_ps)
    log.preview("souscats_id_by_code", souscats_id_by_code)

    return propose_services_sous_categories(
        df_ps=df_ps,
        souscats_id_by_code=souscats_id_by_code,
    )
