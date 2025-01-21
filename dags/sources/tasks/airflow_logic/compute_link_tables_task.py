import logging

from airflow import DAG
from airflow.operators.python import PythonOperator
from sources.tasks.business_logic.compute_link_tables import compute_link_tables
from sources.tasks.business_logic.read_mapping_from_postgres import (
    read_mapping_from_postgres,
)
from utils import logging_utils as log

logger = logging.getLogger(__name__)


def compute_link_tables_task(dag: DAG) -> PythonOperator:
    return PythonOperator(
        task_id="compute_link_tables",
        python_callable=compute_link_tables_wrapper,
        dag=dag,
    )


def compute_link_tables_wrapper(**kwargs):
    df_acteur = kwargs["ti"].xcom_pull(task_ids="propose_acteur_changes")["df"]
    acteurservice_id_by_code = read_mapping_from_postgres(
        table_name="qfdmo_acteurservice"
    )
    labelqualite_id_by_code = read_mapping_from_postgres(
        table_name="qfdmo_labelqualite"
    )
    actions_id_by_code = read_mapping_from_postgres(table_name="qfdmo_action")
    souscats_id_by_code = read_mapping_from_postgres(
        table_name="qfdmo_souscategorieobjet"
    )
    source_id_by_code = read_mapping_from_postgres(table_name="qfdmo_source")
    acteurtype_id_by_code = read_mapping_from_postgres(table_name="qfdmo_acteurtype")

    log.preview("df_acteur", df_acteur)
    log.preview("acteurservice_id_by_code", acteurservice_id_by_code)
    log.preview("labelqualite_id_by_code", labelqualite_id_by_code)
    log.preview("actions_id_by_code", actions_id_by_code)
    log.preview("souscats_id_by_code", souscats_id_by_code)
    log.preview("source_id_by_code", source_id_by_code)
    log.preview("acteurtype_id_by_code", acteurtype_id_by_code)

    df_acteur = compute_link_tables(
        df_acteur=df_acteur,
        acteurservice_id_by_code=acteurservice_id_by_code,
        labelqualite_id_by_code=labelqualite_id_by_code,
        actions_id_by_code=actions_id_by_code,
        souscats_id_by_code=souscats_id_by_code,
        source_id_by_code=source_id_by_code,
        acteurtype_id_by_code=acteurtype_id_by_code,
    )

    log.preview("df_acteur après traitement", df_acteur)

    return df_acteur
