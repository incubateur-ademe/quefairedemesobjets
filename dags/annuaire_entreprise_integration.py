import gzip
import socket
import time
from datetime import datetime

import pandas as pd
import requests
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.providers.postgres.hooks.postgres import PostgresHook

default_args = {
    "owner": "airflow",
    "depends_on_past": False,
    "start_date": datetime(2024, 8, 18),
    "retries": 1,
    "email_on_failure": False,
    "email_on_retry": False,
}

dag = DAG(
    dag_id="annuaire_entreprise_datasets_integration",
    dag_display_name="Téléchargement de la base de données annuaire entreprise",
    default_args=default_args,
    description="Download unités légales and etablissements from data.gouv.fr "
    "and save it to postgresql",
    schedule_interval="@weekly",
)
URL_METADATA_ANNUAIRE_ENTREPRISE = "https://www.data.gouv.fr/api/1/datasets/donnees-des-entreprises-utilisees-dans-lannuaire-des-entreprises"


MAX_RETRIES = 2
WAIT_SECONDS = 5


def fetch_and_process_data(url_title, table_name, index_column, schema, **context):
    pg_hook = PostgresHook(postgres_conn_id="qfdmo-django-db")
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

    for i in range(MAX_RETRIES):
        try:
            with requests.get(url, stream=True, timeout=10) as r:
                r.raise_for_status()
                decompressed_file = gzip.GzipFile(fileobj=r.raw)

                chunk_size = 10000
                dp_iter = pd.read_csv(
                    decompressed_file,
                    chunksize=chunk_size,
                    usecols=schema.keys(),
                    dtype=schema,
                )

                for chunk_number, chunk in enumerate(dp_iter):
                    for retry in range(MAX_RETRIES):
                        try:
                            chunk.to_sql(
                                table_name, con=engine, if_exists="append", index=False
                            )
                            print(f"Chunk {chunk_number + 1} processed successfully.")
                            break  # Break out of retry loop if successful
                        except (requests.exceptions.ConnectionError, socket.timeout):
                            print(
                                f"Chunk {chunk_number + 1} failed,"
                                f" retrying... ({retry + 1}/{MAX_RETRIES})"
                            )
                            time.sleep(WAIT_SECONDS)
                    else:
                        raise RuntimeError(
                            f"Failed to process chunk {chunk_number + 1}"
                            f" after {MAX_RETRIES} retries."
                        )
            break  # Exit retry loop if request and processing succeed

        except requests.exceptions.ConnectionError:
            print("HTTP connection failed, retrying...")
        except socket.timeout:
            print("Download failed due to timeout, retrying...")

        time.sleep(WAIT_SECONDS)
    else:
        print("All retries failed. The data could not be fetched and processed.")

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
