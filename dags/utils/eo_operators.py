from datetime import datetime, timedelta

from airflow import DAG
from airflow.models.baseoperator import chain
from airflow.operators.python import PythonOperator
from utils import dag_eo_utils
from utils.db_tasks import read_data_from_postgres

default_args = {
    "owner": "airflow",
    "depends_on_past": False,
    "start_date": datetime(2024, 3, 23),
    "email_on_failure": False,
    "email_on_retry": False,
    "retries": 1,
}


def fetch_data_from_api_task(dag: DAG) -> PythonOperator:
    return PythonOperator(
        task_id="fetch_data_from_api",
        python_callable=dag_eo_utils.fetch_data_from_api,
        dag=dag,
    )


def load_data_from_postgresql_task(dag: DAG) -> PythonOperator:
    return PythonOperator(
        task_id="load_data_from_postgresql",
        python_callable=dag_eo_utils.load_data_from_postgresql,
        dag=dag,
    )


def read_data_from_postgres_task(
    *,
    dag: DAG,
    table_name: str,
    task_id: str,
    retries: int = 5,
    retry_delay: timedelta = timedelta(minutes=2),
) -> PythonOperator:

    return PythonOperator(
        task_id=task_id,
        python_callable=read_data_from_postgres,
        op_kwargs={"table_name": table_name},
        dag=dag,
        retries=retries,
        retry_delay=retry_delay,
    )


def read_acteur_task(dag: DAG) -> PythonOperator:
    return PythonOperator(
        task_id="read_acteur",
        python_callable=dag_eo_utils.read_acteur,
        dag=dag,
    )


def create_actors_task(dag: DAG) -> PythonOperator:
    return PythonOperator(
        task_id="create_actors",
        python_callable=dag_eo_utils.create_actors,
        dag=dag,
    )


def create_proposition_services_task(dag: DAG) -> PythonOperator:
    return PythonOperator(
        task_id="create_proposition_services",
        python_callable=dag_eo_utils.create_proposition_services,
        dag=dag,
    )


def create_proposition_services_sous_categories_task(dag: DAG) -> PythonOperator:
    return PythonOperator(
        task_id="create_proposition_services_sous_categories",
        python_callable=dag_eo_utils.create_proposition_services_sous_categories,
        dag=dag,
    )


def write_data_task(dag: DAG) -> PythonOperator:
    return PythonOperator(
        task_id="write_data_to_validate_into_dagruns",
        python_callable=dag_eo_utils.write_to_dagruns,
        dag=dag,
    )


def serialize_to_json_task(dag: DAG) -> PythonOperator:
    return PythonOperator(
        task_id="serialize_to_json",
        python_callable=dag_eo_utils.serialize_to_json,
        dag=dag,
    )


def create_labels_task(dag: DAG) -> PythonOperator:
    return PythonOperator(
        task_id="create_labels",
        python_callable=dag_eo_utils.create_labels,
        dag=dag,
    )


def create_acteur_services_task(dag: DAG) -> PythonOperator:
    return PythonOperator(
        task_id="create_acteur_services",
        python_callable=dag_eo_utils.create_acteur_services,
        dag=dag,
    )


def eo_task_chain(dag: DAG) -> None:
    read_tasks = [
        fetch_data_from_api_task(dag),
        read_data_from_postgres_task(
            dag=dag, table_name="qfdmo_acteurtype", task_id="read_acteurtype"
        ),
        read_data_from_postgres_task(
            dag=dag, table_name="qfdmo_source", task_id="read_source"
        ),
        read_data_from_postgres_task(
            dag=dag, table_name="qfdmo_action", task_id="read_action"
        ),
        read_data_from_postgres_task(
            dag=dag, table_name="qfdmo_acteurservice", task_id="read_acteurservice"
        ),
        read_data_from_postgres_task(
            dag=dag,
            table_name="qfdmo_souscategorieobjet",
            task_id="read_souscategorieobjet",
        ),
        read_data_from_postgres_task(
            dag=dag, table_name="qfdmo_labelqualite", task_id="read_labelqualite"
        ),
        load_data_from_postgresql_task(dag),
    ]

    create_tasks = [
        create_proposition_services_task(dag),
        create_labels_task(dag),
        create_acteur_services_task(dag),
    ]

    chain(
        read_tasks,
        read_acteur_task(dag),
        create_actors_task(dag),
        create_tasks,
        create_proposition_services_sous_categories_task(dag),
        serialize_to_json_task(dag),
        write_data_task(dag),
    )
