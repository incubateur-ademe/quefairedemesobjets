from importlib import import_module
from pathlib import Path

from airflow import DAG
from airflow.operators.python import PythonOperator

env = Path(__file__).parent.parent.name

dag_eo_utils = import_module(f"{env}.utils.dag_eo_utils")


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
