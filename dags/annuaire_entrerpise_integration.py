import gzip
import io
from datetime import datetime
from importlib import import_module
from pathlib import Path

import pandas as pd
import requests
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.providers.postgres.hooks.postgres import PostgresHook
from tqdm import tqdm

env = Path(__file__).parent.name
utils = import_module(f"{env}.utils.utils")

# Set up default arguments
default_args = {
    "owner": "airflow",
    "depends_on_past": False,
    "start_date": datetime(2024, 8, 18),
    "retries": 1,
    "email_on_failure": False,
    "email_on_retry": False,
}

# Define the DAG
dag = DAG(
    "annuaire_entreprise_datasets_integration",
    default_args=default_args,
    description="Download unités légales and etablissements from data.gouv.fr "
    "and save it to postgresql",
    schedule_interval="@weekly",
)


# Define the generalized function to fetch and process data
def fetch_and_process_data(url_index, table_name, index_column, schema, **context):
    pg_hook = PostgresHook(postgres_conn_id=utils.get_db_conn_id(__file__))
    engine = pg_hook.get_sqlalchemy_engine()
    conn = pg_hook.get_conn()
    cursor = conn.cursor()

    cursor.execute(f"TRUNCATE TABLE  {table_name};")
    conn.commit()

    metadata_url = "https://www.data.gouv.fr/api/1/datasets/donnees-des-entreprises-utilisees-dans-lannuaire-des-entreprises"
    metadata_response = requests.get(metadata_url)
    metadata_response.raise_for_status()
    metadata = metadata_response.json()

    resources = [
        resource
        for resource in metadata["resources"]
        if resource["type"] != "documentation"
    ]
    urls = [resource["url"] for resource in resources]

    if not urls:
        raise ValueError("No data URLs found in the resources.")

    with requests.get(urls[url_index], stream=True) as r:
        r.raise_for_status()
        decompressed_file = gzip.GzipFile(fileobj=io.BytesIO(r.content))

        chunk_size = 10000
        dp_iter = pd.read_csv(
            decompressed_file, chunksize=chunk_size, usecols=schema.keys(), dtype=schema
        )

        with tqdm(total=0, unit="B", unit_scale=True, unit_divisor=1024) as pbar:
            for chunk in dp_iter:
                chunk.to_sql(table_name, con=engine, if_exists="append", index=False)
                pbar.update(chunk.memory_usage(deep=True).sum())

    cursor.execute(
        f"CREATE INDEX IF NOT EXISTS idx_{index_column} "
        f"ON {table_name}({index_column});"
    )
    conn.commit()

    cursor.close()
    conn.close()


# Define the tasks in the DAG using the generalized function
fetch_and_process_unites_legales_task = PythonOperator(
    task_id="fetch_and_process_unites_legales",
    python_callable=fetch_and_process_data,
    op_kwargs={
        "url_index": 0,
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
        "url_index": 1,
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

# Set the tasks to run
fetch_and_process_unites_legales_task
fetch_and_process_etablissements_task
