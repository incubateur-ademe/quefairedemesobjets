import logging

from airflow import DAG
from airflow.operators.python import PythonOperator
from sources.tasks.airflow_logic.config_management import DAGConfig
from sources.tasks.business_logic.db_read_acteur import db_read_acteur
from utils import logging_utils as log

logger = logging.getLogger(__name__)


def db_read_acteur_task(dag: DAG) -> PythonOperator:
    return PythonOperator(
        task_id="db_read_acteur",
        python_callable=db_read_acteur_wrapper,
        dag=dag,
    )


def db_read_acteur_wrapper(**kwargs):
    df_normalized = kwargs["ti"].xcom_pull(task_ids="source_data_normalize")
    dag_config = DAGConfig.from_airflow_params(kwargs["params"])

    log.preview("df_normalized", df_normalized)
    log.preview("dag_config", dag_config)

    return db_read_acteur(
        df_normalized=df_normalized,
        dag_config=dag_config,
    )
