import json
from datetime import datetime
from importlib import import_module
from pathlib import Path

import pandas as pd
from airflow import DAG
from airflow.models.param import Param
from airflow.operators.python import PythonOperator
from airflow.providers.postgres.hooks.postgres import PostgresHook
from fuzzywuzzy import fuzz

env = Path(__file__).parent.name
utils = import_module(f"{env}.utils.utils")
dag_eo_utils = import_module(f"{env}.utils.dag_eo_utils")
api_utils = import_module(f"{env}.utils.api_utils")
mapping_utils = import_module(f"{env}.utils.mapping_utils")
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
    schedule_interval=None,
)


def fetch_and_parse_data(**context):
    limit = context["params"]["limit"]
    pg_hook = PostgresHook(postgres_conn_id=utils.get_db_conn_id(__file__))
    engine = pg_hook.get_sqlalchemy_engine()
    df_acteur = pd.read_sql("qfdmo_displayedacteur", engine)

    df_acteur = df_acteur[
        (df_acteur["siret"] != "None")
        & (df_acteur["siret"].notna())
        & (df_acteur["siret"] != "")
        & (df_acteur["siret"] != " ")
        & (df_acteur["siret"] != "ZZZ")
        & (df_acteur["statut"] == "ACTIF")
    ]

    df_acteur = df_acteur[
        (df_acteur["adresse"] != "")
        & (df_acteur["adresse"].notnull())
        & (df_acteur["ville"].notnull())
        & (df_acteur["code_postal"].notnull())
        & (df_acteur["adresse"] != "-")
        & (df_acteur["adresse"].str.len() > 5)
        & (df_acteur["code_postal"].str.len() == 5)
        & (df_acteur["statut"] == "ACTIF")
    ]

    df_acteur["full_adresse"] = (
        df_acteur["adresse"]
        .fillna("")
        .str.cat(df_acteur["code_postal"].fillna(""), sep=" ")
        .str.cat(df_acteur["ville"].fillna(""), sep=" ")
    )

    df_acteur["full_adresse"] = df_acteur["full_adresse"].str.strip()
    if limit > 1:
        df_acteur = df_acteur.head(limit)

    return df_acteur


def check_actor_with_adresse(**kwargs):
    df = kwargs["ti"].xcom_pull(task_ids="load_and_filter_actors_data")

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
    df_acteur = kwargs["ti"].xcom_pull(task_ids="load_and_filter_actors_data")

    df_acteur["ae_result"] = df_acteur.apply(
        utils.check_siret_using_annuaire_entreprise, axis=1
    )
    return df_acteur[
        ["identifiant_unique", "siret", "nom", "statut", "ae_result", "full_adresse"]
    ]


def combine_ae_result_dicts(row):
    ae_result_siret = (
        row["ae_result_siret"] if isinstance(row["ae_result_siret"], list) else []
    )
    ae_result_adresse = (
        row["ae_result_adresse"] if isinstance(row["ae_result_adresse"], list) else []
    )

    siret_tuples = [tuple(sorted(d.items())) for d in ae_result_siret]
    adresse_tuples = [tuple(sorted(d.items())) for d in ae_result_adresse]

    unique_dicts = set(siret_tuples + adresse_tuples)

    return [dict(t) for t in unique_dicts]


def update_statut(row):
    for result in row["ae_result"]:
        if (
            row["siret"] == result["siret_candidat"]
            and result["search_by_siret_candidat"]
        ):
            if result["etat_admin_candidat"] == "A":
                return pd.Series(
                    [
                        "ACTIF",
                        result["categorie_naf_candidat"],
                        result["adresse_candidat"],
                    ]
                )
            else:
                return pd.Series(
                    [
                        "SUPPRIME",
                        result["categorie_naf_candidat"],
                        result["adresse_candidat"],
                    ]
                )
    return pd.Series(["SUPPRIME", None, row["full_adresse"]])


def set_cohort_id(row):
    current_nom = row["nom"]
    current_adresse_ae = row["ae_adresse"]
    current_adresse_lvao = row["full_adresse"]
    current_naf = row["categorie_naf"]
    current_siret = row["siret"]
    current_siren = current_siret[:9]
    priorities = {
        "ownership_transferred_matching_category_lvao_address": 10,
        "ownership_transferred_matching_category_ae_address": 9,
        "ownership_transferred_different_category": 8,
        "ownership_transferred_different_names": 7,
        "relocation_same_siren_matching_name_and_naf": 6,
        "relocation_same_siren_matching_name_only": 5,
        "relocation_same_siren_not_matching_name": 4,
        "relocation": 3,
        "closed_0_open_candidates": 2,
        "closed": 1,
    }

    best_outcome = "closed"
    highest_priority_level = 1
    best_candidate_index = -1
    nb_candidats_ouvert = len(
        [res for res in row["ae_result"] if res["etat_admin_candidat"] == "A"]
    )

    for index, candidate in enumerate(row["ae_result"]):
        nom_match_strength = fuzz.ratio(candidate["nom_candidat"], current_nom)
        adresse_lvao_match_ratio = fuzz.ratio(
            candidate["adresse_candidat"], current_adresse_lvao
        )
        adresse_ae_match_ratio = fuzz.ratio(
            candidate["adresse_candidat"], current_adresse_ae
        )
        candidate_siren = candidate["siret_candidat"][:9]
        if (
            adresse_lvao_match_ratio > 80
            and candidate["categorie_naf_candidat"] == current_naf
            and candidate["etat_admin_candidat"] == "A"
            and nom_match_strength > 80
        ):
            best_outcome = "ownership_transferred_matching_category_lvao_address"
            best_candidate_index = index
            break
        elif (
            adresse_ae_match_ratio > 80
            and candidate["categorie_naf_candidat"] == current_naf
            and candidate["etat_admin_candidat"] == "A"
            and nom_match_strength > 80
            and priorities["ownership_transferred_matching_category_ae_address"]
            > highest_priority_level
        ):
            best_outcome = "ownership_transferred_matching_category_ae_address"
            best_candidate_index = index
            break
        elif (
            (adresse_ae_match_ratio > 80 or adresse_lvao_match_ratio > 80)
            and candidate["categorie_naf_candidat"] != current_naf
            and candidate["etat_admin_candidat"] == "A"
            and nom_match_strength > 80
            and priorities["ownership_transferred_different_category"]
            > highest_priority_level
        ):
            best_outcome = "ownership_transferred_different_category"
            highest_priority_level = priorities[best_outcome]
            best_candidate_index = index
        elif (
            (adresse_ae_match_ratio > 80 or adresse_lvao_match_ratio > 80)
            and candidate["categorie_naf_candidat"] == current_naf
            and candidate["etat_admin_candidat"] == "A"
            and priorities["ownership_transferred_different_names"]
            > highest_priority_level
        ):
            best_outcome = "ownership_transferred_different_names"
            highest_priority_level = priorities[best_outcome]
            best_candidate_index = index

        elif (
            candidate["nombre_etablissements_ouverts"] == 1
            and current_siren == candidate_siren
            and candidate["etat_admin_candidat"] == "A"
            and nom_match_strength > 80
            and candidate["categorie_naf_candidat"] == current_naf
            and priorities["relocation_same_siren_matching_name_and_naf"]
            > highest_priority_level
        ):
            best_outcome = "relocation_same_siren_matching_name_and_naf"
            highest_priority_level = priorities[best_outcome]
            best_candidate_index = index

        elif (
            candidate["nombre_etablissements_ouverts"] == 1
            and current_siren == candidate_siren
            and candidate["etat_admin_candidat"] == "A"
            and nom_match_strength > 80
            and priorities["relocation_same_siren_matching_name_only"]
            > highest_priority_level
        ):
            best_outcome = "relocation_same_siren_matching_name_only"
            highest_priority_level = priorities[best_outcome]
            best_candidate_index = index

        elif (
            candidate["nombre_etablissements_ouverts"] == 1
            and current_siren == candidate_siren
            and candidate["etat_admin_candidat"] == "A"
            and priorities["relocation_same_siren_not_matching_name"]
            > highest_priority_level
        ):
            best_outcome = "relocation_same_siren_not_matching_name"
            highest_priority_level = priorities[best_outcome]
            best_candidate_index = index
        elif (
            candidate["adresse_candidat"] != current_adresse_ae
            and candidate["adresse_candidat"] != current_adresse_lvao
            and candidate["categorie_naf_candidat"] == current_naf
            and candidate["etat_admin_candidat"] == "A"
            and nom_match_strength > 80
            and priorities["relocation"] > highest_priority_level
        ):
            best_outcome = "relocation"
            highest_priority_level = priorities[best_outcome]
            best_candidate_index = index

        elif (
            nb_candidats_ouvert == 0
            and priorities["closed_0_open_candidates"] > highest_priority_level
        ):
            best_outcome = "closed_0_open_candidates"
            highest_priority_level = priorities[best_outcome]
            best_candidate_index = index

    if best_candidate_index != -1:
        row["ae_result"][best_candidate_index]["used_for_decision"] = True

    return best_outcome


def combine_actors(**kwargs):
    df_acteur_with_siret = kwargs["ti"].xcom_pull(task_ids="check_with_siret")
    df_acteur_with_adresse = kwargs["ti"].xcom_pull(task_ids="check_with_adresse")

    df = pd.merge(
        df_acteur_with_siret,
        df_acteur_with_adresse,
        on=["identifiant_unique", "nom", "statut", "siret", "full_adresse"],
        how="inner",
        suffixes=("_siret", "_adresse"),
    )

    df["ae_result"] = df.apply(combine_ae_result_dicts, axis=1)
    df[["statut", "categorie_naf", "ae_adresse"]] = df.apply(update_statut, axis=1)
    df = df[df["statut"] == "SUPPRIME"]
    df["cohort_id"] = df.apply(set_cohort_id, axis=1)

    cohort_dfs = {}
    for cohort_id in df["cohort_id"].unique():
        cohort_dfs[cohort_id] = df[df["cohort_id"] == cohort_id]

    return cohort_dfs


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


def enrich_location(**kwargs):
    data = kwargs["ti"].xcom_pull(task_ids="combine_actors")

    for key, df in data.items():
        df = df.apply(enrich_row, axis=1)
        data[key] = df

    return data


def serialize_to_json(**kwargs):
    data = kwargs["ti"].xcom_pull(task_ids="get_location")
    columns = [
        "identifiant_unique",
        "location",
        "statut",
        "ae_result",
        "admin_link",
        "commentaires",
    ]
    dag_run = kwargs["dag_run"]
    serialized_data = {}
    for key, df in data.items():
        df["admin_link"] = df["identifiant_unique"].apply(mapping_utils.construct_url)
        df["commentaires"] = df.apply(
            lambda x: mapping_utils.construct_change_log(dag_run), axis=1
        )
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
    op_kwargs={"event": "UPDATE_ACTOR"},
    dag=dag,
)

serialize_to_json_task = PythonOperator(
    task_id="serialize_actors_to_records",
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
