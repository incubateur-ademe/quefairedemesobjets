import logging

from airflow import DAG
from airflow.operators.python import PythonOperator
from sources.tasks.airflow_logic.config_management import DAGConfig
from sources.tasks.business_logic.db_read_acteur import db_read_acteur
from sources.tasks.business_logic.keep_acteur_changed import keep_acteur_changed
from utils import logging_utils as log

logger = logging.getLogger(__name__)


def keep_acteur_changed_task(dag: DAG) -> PythonOperator:
    return PythonOperator(
        task_id="keep_acteur_changed",
        python_callable=keep_acteur_changed_wrapper,
        dag=dag,
    )


def keep_acteur_changed_wrapper(**kwargs):
    df_normalized = kwargs["ti"].xcom_pull(task_ids="source_data_normalize")
    dag_config = DAGConfig.from_airflow_params(kwargs["params"])

    df_acteur_from_db = db_read_acteur(
        df_normalized=df_normalized,
        dag_config=dag_config,
    )

    log.preview("df_normalized", df_normalized)
    log.preview("df_acteur_from_db", df_acteur_from_db)
    log.preview("dag_config", dag_config)

    df_acteur_from_source, df_acteur_from_db, metadata_columns_updated = (
        keep_acteur_changed(
            df_normalized=df_normalized,
            df_acteur_from_db=df_acteur_from_db,
            dag_config=dag_config,
        )
    )
    kwargs["ti"].xcom_push(key="df_acteur_from_source", value=df_acteur_from_source)
    kwargs["ti"].xcom_push(key="df_acteur_from_db", value=df_acteur_from_db)
    kwargs["ti"].xcom_push(
        key="metadata_columns_updated", value=metadata_columns_updated
    )
