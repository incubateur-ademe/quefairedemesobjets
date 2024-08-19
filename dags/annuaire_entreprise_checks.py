import json
from datetime import datetime
from importlib import import_module
from pathlib import Path

import pandas as pd
from airflow import DAG
from airflow.models.param import Param
from airflow.operators.python import PythonOperator
from airflow.providers.postgres.hooks.postgres import PostgresHook

env = Path(__file__).parent.name
utils = import_module(f"{env}.utils.utils")
dag_eo_utils = import_module(f"{env}.utils.dag_eo_utils")
api_utils = import_module(f"{env}.utils.api_utils")
mapping_utils = import_module(f"{env}.utils.mapping_utils")
siret_control_utils = import_module(f"{env}.utils.siret_control_utils")

pd.set_option("display.max_columns", None)

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
    params={"limit": Param(0, type="integer", description="Limit for data processed")},
    description=(
        "A pipeline to apply checks using annuaire entreprise "
        "API and output data to validation tool"
    ),
    schedule="0 0 1 * *",
)


def fetch_and_parse_data(**context):
    limit = context["params"]["limit"]
    pg_hook = PostgresHook(postgres_conn_id=utils.get_db_conn_id(__file__))
    engine = pg_hook.get_sqlalchemy_engine()
    df_acteur = pd.read_sql("qfdmo_displayedacteur", engine)
    df_acteur["full_adresse"] = (
        df_acteur["adresse"]
        .fillna("")
        .str.cat(df_acteur["code_postal"].fillna(""), sep=" ")
        .str.cat(df_acteur["ville"].fillna(""), sep=" ")
    )

    df_acteur = df_acteur[df_acteur["statut"] == "ACTIF"]
    if limit > 1:
        df_acteur = df_acteur.head(limit)

    good_siret_condition = (
        df_acteur["siret"].notna()
        & (df_acteur["siret"] != "")
        & (df_acteur["siret"] != "None")
        & (df_acteur["siret"] != " ")
        & (df_acteur["siret"] != "ZZZ")
    )
    good_address_condition = (
        df_acteur["adresse"].notna()
        & (df_acteur["ville"].notnull())
        & (df_acteur["adresse"] != "")
        & (df_acteur["adresse"] != "-")
        & (df_acteur["adresse"].str.len() > 5)
        & (df_acteur["code_postal"].str.len() == 5)
    )

    df1 = df_acteur[good_siret_condition & good_address_condition]

    df2 = df_acteur[~good_siret_condition & good_address_condition]
    df3 = df_acteur[good_siret_condition & ~good_address_condition]

    return {
        "ok_siret_ok_adresse": df1,
        "nok_siret_ok_adresse": df2,
        "ok_siret_nok_adresse": df3,
    }


def check_actor_with_adresse(**kwargs):
    data = kwargs["ti"].xcom_pull(task_ids="load_and_filter_actors_data")
    df_ok_siret_ok_adresse = data["ok_siret_ok_adresse"]
    df_nok_siret_ok_adresse = data["nok_siret_ok_adresse"]
    df = pd.concat([df_ok_siret_ok_adresse, df_nok_siret_ok_adresse])

    df["ae_result"] = df.apply(
        lambda x: utils.check_siret_using_annuaire_entreprise(
            x, col="full_adresse", adresse_query_flag=True
        ),
        axis=1,
    )

    return df[
        ["identifiant_unique", "siret", "nom", "statut", "ae_result", "full_adresse"]
    ]


def check_actor_with_siret(**kwargs):
    data = kwargs["ti"].xcom_pull(task_ids="load_and_filter_actors_data")
    df_ok_siret_ok_adresse = data["ok_siret_ok_adresse"]
    df_ok_siret_nok_adresse = data["ok_siret_nok_adresse"]
    df_acteur = pd.concat([df_ok_siret_ok_adresse, df_ok_siret_nok_adresse])

    df_acteur["ae_result"] = df_acteur.apply(
        utils.check_siret_using_annuaire_entreprise, axis=1
    )
    return df_acteur[
        ["identifiant_unique", "siret", "nom", "statut", "ae_result", "full_adresse"]
    ]


def enrich_row(row):
    enriched_ae_result = []
    for item in row["ae_result"]:
        latitude = item.get("latitude_candidat")
        longitude = item.get("longitude_candidat")
        if latitude is not None and longitude is not None:
            location = utils.get_location(latitude, longitude)
            if location:
                item["latitude_candidat"] = location["latitude"]
                item["longitude_candidat"] = location["longitude"]
                item["location_candidat"] = location["location"]
        enriched_ae_result.append(item)
    row["ae_result"] = enriched_ae_result
    return row


def combine_actors(**kwargs):
    df_acteur_with_siret = kwargs["ti"].xcom_pull(task_ids="check_with_siret")
    df_acteur_with_adresse = kwargs["ti"].xcom_pull(task_ids="check_with_adresse")

    df = pd.merge(
        df_acteur_with_siret,
        df_acteur_with_adresse,
        on=["identifiant_unique", "nom", "statut", "siret", "full_adresse"],
        how="outer",
        suffixes=("_siret", "_adresse"),
    )

    cohort_dfs = {}

    df["ae_result"] = df.apply(siret_control_utils.combine_ae_result_dicts, axis=1)
    df[["statut", "categorie_naf", "ae_adresse"]] = df.apply(
        siret_control_utils.update_statut, axis=1
    )
    df = df[df["statut"] == "SUPPRIME"]
    if len(df) > 0:
        df["cohort_id"] = df.apply(siret_control_utils.set_cohort_id, axis=1)
    else:
        return cohort_dfs

    for cohort_id in df["cohort_id"].unique():
        cohort_dfs[cohort_id] = df[df["cohort_id"] == cohort_id]

    return cohort_dfs


def enrich_location(**kwargs):
    data = kwargs["ti"].xcom_pull(task_ids="combine_actors")

    for key, df in data.items():
        df = df.apply(enrich_row, axis=1)
        data[key] = df

    return data


def serialize_to_json(**kwargs):
    data = kwargs["ti"].xcom_pull(task_ids="get_location")
    columns = ["identifiant_unique", "statut", "ae_result", "admin_link"]
    serialized_data = {}
    for key, df in data.items():
        df["admin_link"] = df["identifiant_unique"].apply(
            lambda x: mapping_utils.construct_url(x, env)
        )
        df["event"] = "UPDATE_ACTOR"
        df["row_updates"] = df[columns].apply(
            lambda row: json.dumps(row.to_dict(), default=str), axis=1
        )
        serialized_data[key] = {"df": df, "metadata": {"updated_rows": len(df)}}

    return serialized_data


load_and_filter_data_task = PythonOperator(
    task_id="load_and_filter_actors_data",
    python_callable=fetch_and_parse_data,
    dag=dag,
)

check_siret_task = PythonOperator(
    task_id="check_with_siret",
    python_callable=check_actor_with_siret,
    op_kwargs={},
    dag=dag,
)

check_adresse_task = PythonOperator(
    task_id="check_with_adresse",
    python_callable=check_actor_with_adresse,
    op_kwargs={},
    dag=dag,
)

get_location_task = PythonOperator(
    task_id="get_location",
    python_callable=enrich_location,
    op_kwargs={},
    dag=dag,
)

write_data_task = PythonOperator(
    task_id="write_data_to_validate_into_dagruns",
    python_callable=dag_eo_utils.write_to_dagruns,
    dag=dag,
)

serialize_to_json_task = PythonOperator(
    task_id="serialize_to_json",
    python_callable=serialize_to_json,
    dag=dag,
)

combine_candidates = PythonOperator(
    task_id="combine_actors",
    python_callable=combine_actors,
    dag=dag,
)

(
    load_and_filter_data_task
    >> [check_siret_task, check_adresse_task]
    >> combine_candidates
    >> get_location_task
    >> serialize_to_json_task
    >> write_data_task
)
