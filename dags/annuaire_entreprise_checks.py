from datetime import datetime
from importlib import import_module
from pathlib import Path

from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.providers.postgres.hooks.postgres import PostgresHook
from airflow.models.param import Param
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
    if limit > 1:
        df_acteur = df_acteur.head(limit)

    return df_acteur


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

    df["matching_category_naf"] = df["ae_result"].apply(
        lambda x: (
            x["categorie_naf"] == x["categorie_naf_siege"]
            if isinstance(x, dict)
            and "categorie_naf" in x
            and "categorie_naf_siege" in x
            else False
        )
    )

    df["nombre_etablissements_ouverts"] = df["ae_result"].apply(
        lambda x: (
            x["nombre_etablissements_ouverts"]
            if isinstance(x, dict) and "nombre_etablissements_ouverts" in x
            else None
        )
    )

    df_closed = df[df["nombre_etablissements_ouverts"] == 0]
    df_nb_etab_ouvert_1_matching_naf = df[
        (df["nombre_etablissements_ouverts"] == 1) & (df["matching_category_naf"])
    ]
    df_nb_etab_ouverts_2_plus_matching_naf = df[
        (df["nombre_etablissements_ouverts"] > 1) & (df["matching_category_naf"])
    ]
    df_nb_etab_ouvert_1_not_matching_naf = df[
        (df["nombre_etablissements_ouverts"] == 1) & (~df["matching_category_naf"])
    ]
    df_nb_etab_ouverts_2_plus_not_matching_naf = df[
        (df["nombre_etablissements_ouverts"] > 1) & (~df["matching_category_naf"])
    ]
    df_closed["adresse"] = None
    # flake8: noqa: E501
    return {
        "df_closed": df_closed,
        "df_nb_etab_ouvert_1_and_matching_naf": df_nb_etab_ouvert_1_matching_naf,
        "df_nb_etab_ouverts_2_plus_and_matching_naf": df_nb_etab_ouverts_2_plus_matching_naf,
        "df_nb_etab_ouverts_1_and_not_matching_naf": df_nb_etab_ouvert_1_not_matching_naf,
        "df_nb_etab_ouverts_2_plus_and_not_matching_naf": df_nb_etab_ouverts_2_plus_not_matching_naf,
    }


def enrich_lat_lon_ban_api(**kwargs):
    data = kwargs["ti"].xcom_pull(task_ids="check_siret")

    for key, df in data.items():
        if len(df) > 0 and key != "df_closed":
            df["adresse"] = df["ae_result"].apply(
                lambda x: (
                    x["adresse"] if isinstance(x, dict) and "adresse" in x else None
                )
            )

            df["location"] = df.apply(utils.get_location, axis=1)
    return data


def construct_url(identifiant):
    base_url = "https://quefairedemesobjets-preprod.osc-fr1.scalingo.io/admin/qfdmo/displayedacteur/{}/change/"
    return base_url.format(identifiant)


def construct_change_log(dag_run):
    change_log = {
        "message": "Acteur supprimé après vérification sur annuaire entreprise",
        "deleted_by": dag_run.run_id,
        "dag_name": dag_run.dag_id,
        "timestamp": datetime.utcnow().isoformat(),
    }

    return json.dumps(change_log, indent=2)


def serialize_to_json(**kwargs):
    data = kwargs["ti"].xcom_pull(task_ids="check_siret")
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
        df["admin_link"] = df["identifiant_unique"].apply(construct_url)
        df["commentaires"] = df.apply(lambda x: construct_change_log(dag_run), axis=1)
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
    task_id="check_siret",
    python_callable=check_siret,
    op_kwargs={},
    dag=dag,
)

get_lat_lon_using_ban_api = PythonOperator(
    task_id="get_lat_lon_using_ban_api",
    python_callable=enrich_lat_lon_ban_api,
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
    >> get_lat_lon_using_ban_api
    >> serialize_to_json_task
    >> write_data_task
)
