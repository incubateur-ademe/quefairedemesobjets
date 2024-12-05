import json
from datetime import datetime

import pandas as pd
import utils.base_utils as base_utils
import utils.mapping_utils as mapping_utils
import utils.siret_control_utils as siret_control_utils
from airflow import DAG
from airflow.models.param import Param
from airflow.operators.python import PythonOperator
from shared.tasks.airflow_logic.write_data_task import write_data_task
from shared.tasks.database_logic.db_manager import PostgresConnectionManager

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
    dag_id="annuaire_entreprise_checks",
    dag_display_name="Vérification des données avec l'API Annuaire Entreprise",
    default_args=default_args,
    params={
        "limit": Param(0, type="integer", description="Limit for data processed"),
        "source_code_naf": {
            "Ordre National Des Pharmaciens": "47.73Z",
            "Bibliothèques - Ministère de la culture": "84.11Z,91.01Z",
            "Lunettes de Zac": "47.78A",
            "Association des Ludothèques Françaises": "91.01Z,93.29Z",
            "ALIAPUR": "45.31Z",
        },
    },
    description=(
        "A pipeline to apply checks using annuaire entreprise "
        "API and output data to validation tool"
    ),
    schedule="0 0 1 * *",
)


def fetch_and_parse_data(**context):
    limit = context["params"]["limit"]
    engine = PostgresConnectionManager().engine
    active_actors_query = """
        SELECT
            da.*,
            s.code AS source_code
        FROM
            qfdmo_displayedacteur da
        JOIN
            qfdmo_source s
        ON
            da.source_id = s.id
        WHERE
            da.statut = 'ACTIF';
    """
    df_acteur = pd.read_sql(active_actors_query, engine)

    if limit > 1:
        df_acteur = df_acteur.head(limit)

    good_siret_closed_query = """
        SELECT
            a.*,
            e.etat_administratif,
            s.code AS source_code
        FROM
            qfdmo_displayedacteur a
        LEFT JOIN
            etablissements e
        ON
            a.siret = e.siret
        LEFT JOIN
            qfdmo_source s
        ON
            a.source_id = s.id
        WHERE
            a.statut = 'ACTIF'
            AND LENGTH(a.siret) = 14
            AND e.etat_administratif = 'F'
    """
    df_good_siret_closed = pd.read_sql(good_siret_closed_query, engine)

    good_address_condition = (
        df_acteur["adresse"].notna()
        & (df_acteur["ville"].notnull())
        & (df_acteur["adresse"] != "")
        & (df_acteur["adresse"] != "-")
        & (df_acteur["adresse"].str.len() > 5)
        & (df_acteur["code_postal"].str.len() == 5)
    )

    df_a_siretiser = df_acteur[
        (
            ~df_acteur["identifiant_unique"].isin(
                df_good_siret_closed["identifiant_unique"]
            )
        )
        & (good_address_condition)
        & (df_acteur["siret"].str.len() != 14)
        & (df_acteur["siret"].str.len() != 9)
    ]
    print("df_good_siret_closed size:", df_good_siret_closed.shape)
    print("df_a_siretiser size:", df_a_siretiser.shape)
    return {
        "closed_ok_siret": df_good_siret_closed,
        "nok_siret_ok_adresse": df_a_siretiser,
    }


def check_actor_with_adresse(**kwargs):
    data = kwargs["ti"].xcom_pull(task_ids="load_and_filter_actors_data")
    source_code_naf = kwargs["params"]["source_code_naf"]
    df_ok_siret_ok_adresse = data["closed_ok_siret"]
    df_nok_siret_ok_adresse = data["nok_siret_ok_adresse"]
    df = pd.concat([df_ok_siret_ok_adresse, df_nok_siret_ok_adresse])
    df["full_adresse"] = mapping_utils.create_full_adresse(df)
    df["naf_code"] = df["source_code"].map(source_code_naf)

    df["ae_result"] = df.apply(
        lambda x: base_utils.check_siret_using_annuaire_entreprise(
            x, query_col="full_adresse", naf_col="naf_code", adresse_query_flag=True
        ),
        axis=1,
    )

    return df[
        [
            "identifiant_unique",
            "siret",
            "nom",
            "statut",
            "ae_result",
            "full_adresse",
            "source_code",
            "naf_code",
        ]
    ]


def check_actor_with_siret(**kwargs):
    data = kwargs["ti"].xcom_pull(task_ids="load_and_filter_actors_data")
    df_acteur = data["closed_ok_siret"]
    df_acteur["full_adresse"] = mapping_utils.create_full_adresse(df_acteur)
    df_acteur["ae_result"] = df_acteur.apply(
        base_utils.check_siret_using_annuaire_entreprise, axis=1
    )
    return df_acteur[
        [
            "identifiant_unique",
            "siret",
            "nom",
            "statut",
            "ae_result",
            "full_adresse",
            "source_code",
        ]
    ]


def enrich_row(row):
    enriched_ae_result = []
    for item in row.get("ae_result", []):
        latitude = item.get("latitude_candidat")
        longitude = item.get("longitude_candidat")
        if latitude is not None and longitude is not None:
            location = base_utils.get_location(latitude, longitude)
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
        on=[
            "identifiant_unique",
            "nom",
            "statut",
            "siret",
            "full_adresse",
            "source_code",
        ],
        how="outer",
        suffixes=("_siret", "_adresse"),
    )

    cohort_dfs = {}

    df_bad_siret = df[
        df["ae_result_siret"].isnull()
        & df["full_adresse"].notnull()
        & (df["siret"].str.len() != 14)
        & (df["siret"].str.len() != 9)
    ]

    if not df_bad_siret.empty:
        df_bad_siret["ae_result"] = df_bad_siret.apply(
            siret_control_utils.combine_ae_result_dicts, axis=1
        )
        df_non_empty_ae_results = df_bad_siret[
            df_bad_siret["ae_result"].apply(
                lambda x: len(
                    [
                        candidate
                        for candidate in x
                        if candidate["etat_admin_candidat"] == "A"
                    ]
                )
                > 0
            )
        ]
        df_non_empty_ae_results["naf_code"] = df_non_empty_ae_results[
            "naf_code_adresse"
        ]
        df_empty_ae_results = df_bad_siret[
            df_bad_siret["ae_result"].apply(lambda x: len(x) == 0)
        ]
        for (source_code, source_code_naf), group in df_non_empty_ae_results.groupby(
            [
                df_non_empty_ae_results["source_code"].fillna("None"),
                df_non_empty_ae_results["naf_code"].fillna("None"),
            ]
        ):
            cohort_name = (
                f"siretitsation_with_adresse_bad_siret_source_"
                f"{source_code}_naf_{source_code_naf}"
            )
            cohort_dfs[cohort_name] = group

        cohort_dfs["siretitsation_with_adresse_bad_siret_empty"] = df_empty_ae_results

    df = df[~df["identifiant_unique"].isin(df_bad_siret["identifiant_unique"])]

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

    for cohort_id, cohort_df in cohort_dfs.items():
        print(f"Cohort ID: {cohort_id} - Number of rows: {len(cohort_df)}")

    return cohort_dfs


def enrich_location(**kwargs):
    data = kwargs["ti"].xcom_pull(task_ids="combine_actors")

    for key, df in data.items():
        df = df.apply(enrich_row, axis=1)
        data[key] = df

    return data


def db_data_prepare(**kwargs):
    data = kwargs["ti"].xcom_pull(task_ids="get_location")
    columns = ["identifiant_unique", "statut", "ae_result", "admin_link"]
    serialized_data = {}
    for key, df in data.items():
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


serialize_to_json_task = PythonOperator(
    task_id="db_data_prepare",
    python_callable=db_data_prepare,
    dag=dag,
)

combine_candidates = PythonOperator(
    task_id="combine_actors",
    python_callable=combine_actors,
    dag=dag,
)

(
    load_and_filter_data_task
    >> check_siret_task
    >> check_adresse_task
    >> combine_candidates
    >> get_location_task
    >> serialize_to_json_task
    >> write_data_task(dag)
)
