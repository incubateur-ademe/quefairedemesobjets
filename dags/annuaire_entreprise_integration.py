import gzip
from datetime import datetime
from importlib import import_module
from pathlib import Path

import pandas as pd
import requests
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.providers.postgres.hooks.postgres import PostgresHook

env = Path(__file__).parent.name
utils = import_module(f"{env}.utils.utils")

default_args = {
    "owner": "airflow",
    "depends_on_past": False,
    "start_date": datetime(2024, 8, 18),
    "retries": 1,
    "email_on_failure": False,
    "email_on_retry": False,
}

dag = DAG(
    "annuaire_entreprise_datasets_integration",
    default_args=default_args,
    description="Download unités légales and etablissements from data.gouv.fr "
    "and save it to postgresql",
    schedule_interval="@weekly",
)
URL_METADATA_ANNUAIRE_ENTREPRISE = "https://www.data.gouv.fr/api/1/datasets/donnees-des-entreprises-utilisees-dans-lannuaire-des-entreprises"


def fetch_and_process_data(url_title, table_name, index_column, schema, **context):
    pg_hook = PostgresHook(postgres_conn_id=utils.get_db_conn_id(__file__))
    engine = pg_hook.get_sqlalchemy_engine()

    with pg_hook.get_conn() as conn:
        with conn.cursor() as cursor:
            cursor.execute(f"TRUNCATE TABLE {table_name};")
            conn.commit()

    metadata_url = URL_METADATA_ANNUAIRE_ENTREPRISE
    metadata_response = requests.get(metadata_url)
    metadata_response.raise_for_status()
    metadata = metadata_response.json()

    resources = [
        resource
        for resource in metadata["resources"]
        if resource["type"] != "documentation"
    ]

    url = next(
        (resource["url"] for resource in resources if url_title in resource["title"]),
        None,
    )

    if not url:
        raise ValueError("No data URLs found in the resources.")

    with requests.get(url, stream=True) as r:
        r.raise_for_status()
        decompressed_file = gzip.GzipFile(fileobj=r.raw)

        chunk_size = 10000
        dp_iter = pd.read_csv(
            decompressed_file, chunksize=chunk_size, usecols=schema.keys(), dtype=schema
        )

        for chunk in dp_iter:
            chunk.to_sql(table_name, con=engine, if_exists="append", index=False)

    with pg_hook.get_conn() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                f"CREATE INDEX IF NOT EXISTS idx_{index_column} "
                f"ON {table_name}({index_column});"
            )
            conn.commit()


fetch_and_process_unites_legales_task = PythonOperator(
    task_id="fetch_and_process_unites_legales",
    python_callable=fetch_and_process_data,
    op_kwargs={
        "url_title": "unites-legales",
        "table_name": "unites_legales",
        "index_column": "siret_siege",
        "schema": {
            "siren": "str",
            "siret_siege": "str",
            "etat_administratif": "str",
            "statut_diffusion": "str",
            "nombre_etablissements": "float",
            "nombre_etablissements_ouverts": "float",
            "nom_complet": "str",
            "est_ess": "bool",
        },
    },
    dag=dag,
)

fetch_and_process_etablissements_task = PythonOperator(
    task_id="fetch_and_process_etablissements",
    python_callable=fetch_and_process_data,
    op_kwargs={
        "url_title": "etablissements",
        "table_name": "etablissements",
        "index_column": "siret",
        "schema": {
            "siren": "str",
            "siret": "str",
            "est_siege": "bool",
            "adresse": "str",
            "etat_administratif": "str",
            "statut_diffusion": "str",
            "latitude": "float",
            "longitude": "float",
        },
    },
    dag=dag,
)

fetch_and_process_unites_legales_task
fetch_and_process_etablissements_task
