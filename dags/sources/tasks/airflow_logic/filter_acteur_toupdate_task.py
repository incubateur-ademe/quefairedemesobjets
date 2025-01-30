import logging

from airflow import DAG
from airflow.operators.python import PythonOperator
from sources.tasks.airflow_logic.config_management import DAGConfig
from sources.tasks.business_logic.filter_acteur_toupdate import filter_acteur_toupdate
from utils import logging_utils as log

logger = logging.getLogger(__name__)


def filter_acteur_toupdate_task(dag: DAG) -> PythonOperator:
    return PythonOperator(
        task_id="filter_acteur_toupdate",
        python_callable=filter_acteur_toupdate_wrapper,
        dag=dag,
    )


def filter_acteur_toupdate_wrapper(**kwargs):
    df_normalized = kwargs["ti"].xcom_pull(task_ids="source_data_normalize")
    df_acteur_from_db = kwargs["ti"].xcom_pull(task_ids="db_read_acteur")
    dag_config = DAGConfig.from_airflow_params(kwargs["params"])

    log.preview("df_normalized", df_normalized)
    log.preview("df_acteur_from_db", df_acteur_from_db)
    log.preview("dag_config", dag_config)

    return filter_acteur_toupdate(
        df_normalized=df_normalized,
        df_acteur_from_db=df_acteur_from_db,
        dag_config=dag_config,
    )
