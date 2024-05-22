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
    df_acteur = pd.read_sql("qfdmo_displayedacteur", engine)
    df_acteur = df_acteur[
        (df_acteur["siret"] != "None")
        & (df_acteur["siret"].notna())
        & (df_acteur["siret"] != "")
        & (df_acteur["siret"] != "ZZZ")
        & (df_acteur["statut"] == "ACTIF")
    ]
    return df_acteur.head(1000)


def check_siret(**kwargs):
    df = kwargs["ti"].xcom_pull(task_ids="load_and_filter_actors_data")
    df["ae_result"] = df.apply(utils.check_siret_using_annuaire_entreprise, axis=1)
    df["etat_admin"] = df["ae_result"].apply(
        lambda x: x["etat_admin"] if isinstance(x, dict) and "etat_admin" in x else None
    )
    df["siret_siege"] = df["ae_result"].apply(
        lambda x: (
            x["siret_siege"] if isinstance(x, dict) and "siret_siege" in x else None
        )
    )

    df_closed = df[(df["etat_admin"] == "F") & (df["siret_siege"].isna())]
    df_moved = df[(df["etat_admin"] == "F") & (df["siret_siege"].notna())]

    return {"df_closed": df_closed, "df_moved": df_moved}


def construct_url(identifiant):
    base_url = "https://quefairedemesobjets-preprod.osc-fr1.scalingo.io/admin/qfdmo/displayedacteur/{}/change/"
    return base_url.format(identifiant)


def serialize_to_json(**kwargs):
    data = kwargs["ti"].xcom_pull(task_ids="check_siret")
    columns = ["identifiant_unique", "statut", "ae_result", "admin_link"]

    df_closed = data["df_closed"]
    df_moved = data["df_moved"]

    df_moved["admin_link"] = df_moved["identifiant_unique"].apply(construct_url)
    df_closed["admin_link"] = df_closed["identifiant_unique"].apply(construct_url)

    df_closed["row_updates"] = df_closed[columns].apply(
        lambda row: json.dumps(row.to_dict(), default=str), axis=1
    )
    df_moved["row_updates"] = df_moved[columns].apply(
        lambda row: json.dumps(row.to_dict(), default=str), axis=1
    )

    return {
        "closed": {"df": df_closed, "metadata": {"added_rows": len(df_closed)}},
        "moved": {"df": df_moved, "metadata": {"added_rows": len(df_moved)}},
    }


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
    op_kwargs={"event": "UPDATE_ACTOR"},
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