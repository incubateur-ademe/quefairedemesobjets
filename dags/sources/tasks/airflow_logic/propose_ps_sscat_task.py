import logging

from airflow import DAG
from airflow.operators.python import PythonOperator
from sources.tasks.business_logic.propose_ps_sscat import propose_ps_sscat
from utils import logging_utils as log

logger = logging.getLogger(__name__)


def propose_ps_sscat_task(dag: DAG) -> PythonOperator:
    return PythonOperator(
        task_id="propose_ps_sscat",
        python_callable=propose_ps_sscat_wrapper,
        dag=dag,
    )


def propose_ps_sscat_wrapper(**kwargs):
    df_ps = kwargs["ti"].xcom_pull(task_ids="propose_ps")["df"]
    souscats_id_by_code = kwargs["ti"].xcom_pull(task_ids="db_read_souscategorieobjet")
    params = kwargs["params"]
    product_mapping = params.get("product_mapping", {})

    log.preview("df_ps", df_ps)
    log.preview("souscats_id_by_code", souscats_id_by_code)
    log.preview("product_mapping", product_mapping)

    return propose_ps_sscat(
        df_ps=df_ps,
        souscats_id_by_code=souscats_id_by_code,
        product_mapping=product_mapping,
    )
