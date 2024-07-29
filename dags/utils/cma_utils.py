import json
import logging
from datetime import datetime
from importlib import import_module
from pathlib import Path
import requests
import pandas as pd
from airflow.operators.python import PythonOperator
from airflow import DAG
import re

logger = logging.getLogger(__name__)

env = Path(__file__).parent.parent.name

utils = import_module(f"{env}.utils.utils")
api_utils = import_module(f"{env}.utils.api_utils")
mapping_utils = import_module(f"{env}.utils.mapping_utils")


def get_data_from_artisanat_api(limit=100, offset=100):
    url = "https://data.artisanat.fr/api/explore/v2.1/catalog/datasets/reparacteurs/records"
    params = {
        "limit": limit,
        "offset": offset,
    }

    response = requests.get(url, params=params)
    if response.status_code == 200:
        data = response.json()
        return data
    else:
        response.raise_for_status()


def fetch_data_task(dag: DAG) -> PythonOperator:
    return PythonOperator(
        task_id="fetch_data_from_api",
        python_callable=get_cma_dataset,
        dag=dag,
    )


def clean_float(value):
    if isinstance(value, str):
        value = re.sub(r",$", "", value).replace(",", ".")
    try:
        return float(value)
    except ValueError:
        return None


def create_actors_task(dag: DAG) -> PythonOperator:
    return PythonOperator(
        task_id="create_actors",
        python_callable=create_actors,
        dag=dag,
    )


def combine_categories(row):
    categories = [row["categorie"], row["categorie2"], row["categorie3"]]
    categories = [cat for cat in categories if pd.notna(cat)]
    return " | ".join(categories)


def prefix_url(url):
    if url is None:
        return None
    elif url.startswith("http://") or url.startswith("https://"):
        return url
    else:
        return "https://" + url


def get_cma_dataset():
    total_records = get_data_from_artisanat_api(limit=1, offset=0)["total_count"]
    records_per_request = 100
    all_data = []

    for offset in range(0, total_records, records_per_request):
        data = get_data_from_artisanat_api(limit=records_per_request, offset=offset)
        all_data.extend(data["results"])
    df = pd.DataFrame(all_data)
    df["produitsdechets_acceptes"] = df.apply(combine_categories, axis=1)

    return df


def create_actors(**kwargs):
    data_dict = kwargs["ti"].xcom_pull(task_ids="load_data_from_postgresql")
    df = kwargs["ti"].xcom_pull(task_ids="fetch_data_from_api")
    df_sources = data_dict["sources"]
    df_acteurtype = data_dict["acteurtype"]
    config_path = Path(__file__).parent.parent / "config" / "db_mapping.json"

    with open(config_path, "r") as f:
        config = json.load(f)

    params = kwargs["params"]
    column_mapping = params["column_mapping"]

    df["source_id"] = mapping_utils.get_id_from_code(
        "CMA - Chambre des métiers et de l'artisanat", df_sources
    )
    df["label_code"] = "reparacteur"

    df["latitude"] = df["latitude"].apply(clean_float)
    df["longitude"] = df["longitude"].apply(clean_float)
    df["type_de_point_de_collecte"] = None
    df["location"] = df.apply(
        lambda row: utils.transform_location(row["longitude"], row["latitude"]),
        axis=1,
    )
    df["acteur_type_id"] = mapping_utils.transform_acteur_type_id(
        "artisan, commerce indépendant", df_acteurtype=df_acteurtype
    )
    for old_col, new_col in column_mapping.items():
        if new_col:
            if old_col == "latitude" or old_col == "longitude":
                continue
            elif old_col == "id":
                df[new_col] = "CMA_REPARACTEUR_" + df["id"].astype(str)
            elif old_col == "is_enabled":
                df[new_col] = df[old_col].map({1: "ACTIF", 0: "SUPPRIME"})
            else:
                df[new_col] = df[old_col]
    df["identifiant_unique"] = df.apply(
        lambda x: mapping_utils.create_identifiant_unique(
            x, source_name="CMA_REPARACTEUR"
        ),
        axis=1,
    )

    # Apply the function to the URL column
    df["url"] = df["url"].apply(prefix_url)
    df["point_de_reparation"] = True
    date_creation = datetime.now()
    df["cree_le"] = date_creation
    df["statut"] = "ACTIF"
    df["modifie_le"] = df["cree_le"]
    df["labels_etou_bonus"] = "Agréé Bonus Réparation"

    df = df.drop_duplicates(subset="siret", keep="first")

    metadata = {
        "added_rows": len(df),
    }

    return {"df": df, "metadata": metadata, "config": config}
