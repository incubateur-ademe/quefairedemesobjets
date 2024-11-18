from datetime import datetime, timedelta

from airflow import DAG
from airflow.models.baseoperator import chain
from airflow.operators.python import PythonOperator
from airflow.utils.trigger_rule import TriggerRule
from sources.tasks.db_read_acteur import db_read_acteur_task
from sources.tasks.propose_services import propose_services_task
from sources.tasks.source_config_validate import source_config_validate
from sources.tasks.source_data_download import source_data_download
from sources.tasks.source_data_normalize import source_data_normalize_wrapper
from sources.tasks.source_data_validate import source_data_validate
from utils import dag_eo_utils
from utils.db_tasks import read_mapping_from_postgres

default_args = {
    "owner": "airflow",
    "depends_on_past": False,
    "start_date": datetime(2024, 3, 23),
    "email_on_failure": False,
    "email_on_retry": False,
    "retries": 1,
}


def source_config_validate_task(dag: DAG) -> PythonOperator:
    return PythonOperator(
        task_id="source_config_validate",
        python_callable=source_config_validate,
        dag=dag,
        trigger_rule=TriggerRule.ALL_SUCCESS,
        retries=0,
    )


def source_data_download_task(dag: DAG) -> PythonOperator:
    return PythonOperator(
        task_id="source_data_download",
        python_callable=source_data_download,
        dag=dag,
        trigger_rule=TriggerRule.ALL_SUCCESS,
        retries=0,
    )


def source_data_normalize_task(dag: DAG) -> PythonOperator:
    return PythonOperator(
        task_id="source_data_normalize",
        python_callable=source_data_normalize_wrapper,
        dag=dag,
        trigger_rule=TriggerRule.ALL_SUCCESS,
        retries=0,
    )


def source_data_validate_task(dag: DAG) -> PythonOperator:
    return PythonOperator(
        task_id="source_data_validate",
        python_callable=source_data_validate,
        dag=dag,
        trigger_rule=TriggerRule.ALL_SUCCESS,
        retries=0,
    )


def db_read_propositions_max_id_task(dag: DAG) -> PythonOperator:
    return PythonOperator(
        task_id="db_read_propositions_max_id",
        python_callable=dag_eo_utils.db_read_propositions_max_id,
        dag=dag,
    )


def read_mapping_from_postgres_task(
    *,
    dag: DAG,
    table_name: str,
    task_id: str,
    retries: int = 0,
    retry_delay: timedelta = timedelta(minutes=2),
) -> PythonOperator:

    return PythonOperator(
        task_id=task_id,
        python_callable=read_mapping_from_postgres,
        op_kwargs={"table_name": table_name},
        dag=dag,
        retries=retries,
        retry_delay=retry_delay,
    )


def read_acteur_task(dag: DAG) -> PythonOperator:
    return PythonOperator(
        task_id="db_read_acteur",
        python_callable=db_read_acteur_task,
        dag=dag,
    )


def create_actors_task(dag: DAG) -> PythonOperator:
    return PythonOperator(
        task_id="propose_acteur_changes",
        python_callable=dag_eo_utils.propose_acteur_changes,
        dag=dag,
    )


def get_acteur_to_delete_task(dag: DAG) -> PythonOperator:
    return PythonOperator(
        task_id="propose_acteur_to_delete",
        python_callable=dag_eo_utils.propose_acteur_to_delete,
        dag=dag,
    )


def create_proposition_services_task(dag: DAG) -> PythonOperator:
    return PythonOperator(
        task_id="propose_services",
        python_callable=propose_services_task,
        dag=dag,
    )


def create_proposition_services_sous_categories_task(dag: DAG) -> PythonOperator:
    return PythonOperator(
        task_id="propose_services_sous_categories",
        python_callable=dag_eo_utils.propose_services_sous_categories,
        dag=dag,
    )


def write_data_task(dag: DAG) -> PythonOperator:
    return PythonOperator(
        task_id="db_data_write",
        python_callable=dag_eo_utils.write_to_dagruns,
        dag=dag,
    )


def serialize_to_json_task(dag: DAG) -> PythonOperator:
    return PythonOperator(
        task_id="db_data_prepare",
        python_callable=dag_eo_utils.db_data_prepare,
        dag=dag,
    )


def create_labels_task(dag: DAG) -> PythonOperator:
    return PythonOperator(
        task_id="propose_labels",
        python_callable=dag_eo_utils.propose_labels,
        dag=dag,
    )


def create_acteur_services_task(dag: DAG) -> PythonOperator:
    return PythonOperator(
        task_id="propose_acteur_services",
        python_callable=dag_eo_utils.propose_acteur_services,
        dag=dag,
    )


def eo_task_chain(dag: DAG) -> None:
    read_tasks = [
        read_mapping_from_postgres_task(
            dag=dag, table_name="qfdmo_acteurtype", task_id="db_read_acteurtype"
        ),
        read_mapping_from_postgres_task(
            dag=dag, table_name="qfdmo_source", task_id="db_read_source"
        ),
        read_mapping_from_postgres_task(
            dag=dag, table_name="qfdmo_action", task_id="db_read_action"
        ),
        read_mapping_from_postgres_task(
            dag=dag, table_name="qfdmo_acteurservice", task_id="db_read_acteurservice"
        ),
        read_mapping_from_postgres_task(
            dag=dag, table_name="qfdmo_labelqualite", task_id="db_read_labelqualite"
        ),
        read_mapping_from_postgres_task(
            dag=dag,
            table_name="qfdmo_souscategorieobjet",
            task_id="db_read_souscategorieobjet",
        ),
        db_read_propositions_max_id_task(dag),
    ]

    create_tasks = [
        create_proposition_services_task(dag),
        create_labels_task(dag),
        create_acteur_services_task(dag),
    ]

    chain(
        # Spécifique à la source pour amener à
        # un état normalisé et validé des données
        source_config_validate_task(dag),
        source_data_download_task(dag),
        source_data_normalize_task(dag),
        source_data_validate_task(dag),
        # Logique commune à toutes les sources
        read_tasks,
        read_acteur_task(dag),
        create_actors_task(dag),
        get_acteur_to_delete_task(dag),
        create_tasks,
        create_proposition_services_sous_categories_task(dag),
        serialize_to_json_task(dag),
        write_data_task(dag),
    )
