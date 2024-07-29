import logging
from datetime import datetime
from importlib import import_module
from pathlib import Path
from airflow.operators.python import PythonOperator
from airflow import DAG

logger = logging.getLogger(__name__)

env = Path(__file__).parent.parent.name

utils = import_module(f"{env}.utils.utils")
api_utils = import_module(f"{env}.utils.api_utils")
mapping_utils = import_module(f"{env}.utils.mapping_utils")


def create_reparacteur_task(dag: DAG) -> PythonOperator:
    return PythonOperator(
        task_id="create_actors",
        python_callable=create_reparacteurs,
        dag=dag,
    )


def create_reparacteurs(**kwargs):
    data_dict = kwargs["ti"].xcom_pull(task_ids="load_data_from_postgresql")
    df = kwargs["ti"].xcom_pull(task_ids="fetch_data_from_api")
    df_sources = data_dict["sources"]
    df_acteurtype = data_dict["acteurtype"]
    df["produitsdechets_acceptes"] = df.apply(mapping_utils.combine_categories, axis=1)

    config = utils.get_mapping_config()

    params = kwargs["params"]
    column_mapping = params["column_mapping"]

    df["source_id"] = mapping_utils.get_id_from_code(
        "CMA - Chambre des métiers et de l'artisanat", df_sources
    )
    df["label_code"] = "reparacteur"

    df["latitude"] = df["latitude"].apply(mapping_utils.clean_float_from_fr_str)
    df["longitude"] = df["longitude"].apply(mapping_utils.clean_float_from_fr_str)
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

    df["url"] = df["url"].apply(mapping_utils.prefix_url)
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
