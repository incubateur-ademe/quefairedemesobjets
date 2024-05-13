from datetime import datetime
from importlib import import_module
from pathlib import Path

from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.providers.postgres.hooks.postgres import PostgresHook
import pandas as pd
import json

env = Path(__file__).parent.name
utils = import_module(f"{env}.utils.utils")
dag_eo_utils = import_module(f"{env}.utils.dag_eo_utils")
api_utils = import_module(f"{env}.utils.api_utils")

default_args = {
    "owner": "airflow",
    "depends_on_past": False,
    "start_date": datetime(2024, 3, 23),
    "email_on_failure": False,
    "email_on_retry": False,
    "retries": 1,
}

dag = DAG(
    utils.get_dag_name(__file__, "annuaire_entreprise_checks"),
    default_args=default_args,
    description=(
        "A pipeline to apply checks using annuaire entreprise "
        "API and output data to validation tool"
    ),
    schedule_interval=None,
)


def fetch_and_parse_data(**context):
    pg_hook = PostgresHook(postgres_conn_id=utils.get_db_conn_id(__file__))
    engine = pg_hook.get_sqlalchemy_engine()
    df_acteur = pd.read_sql("qfdmo_acteur", engine)
    df_acteur = df_acteur[
        (df_acteur["siret"] != "None")
        & (df_acteur["siret"].notna())
        & (df_acteur["siret"] != "")
        & (df_acteur["siret"] != "ZZZ")
    ]

    return df_acteur


def check_siret(**kwargs):
    df = kwargs["ti"].xcom_pull(task_ids="load_and_filter_actors_data")
    df["etat_admin"] = df.apply(utils.check_siret_using_annuaire_entreprise, axis=1)
    df = df[df["etat_admin"] == "F"]
    df["statut"] = "SUPPRIME"
    return df


def serialize_to_json(**kwargs):
    df_actors = kwargs["ti"].xcom_pull(task_ids="check_siret")

    df_actors["row_updates"] = df_actors.apply(
        lambda row: json.dumps(row.to_dict(), default=str), axis=1
    )

    return df_actors


load_and_filter_data_task = PythonOperator(
    task_id="load_and_filter_actors_data",
    python_callable=fetch_and_parse_data,
    dag=dag,
)

check_siret_task = PythonOperator(
    task_id="check_siret",
    python_callable=check_siret,
    op_kwargs={},
    dag=dag,
)

write_data_task = PythonOperator(
    task_id="write_data_to_validate_into_dagruns",
    python_callable=dag_eo_utils.write_to_dagruns,
    dag=dag,
)

serialize_to_json_task = PythonOperator(
    task_id="serialize_actors_to_records",
    python_callable=serialize_to_json,
    dag=dag,
)

(
    load_and_filter_data_task
    >> check_siret_task
    >> serialize_to_json_task
    >> write_data_task
)
