from datetime import datetime
from importlib import import_module
from pathlib import Path

from airflow import DAG

env = Path(__file__).parent.name
utils = import_module(f"{env}.utils.utils")
eo_operators = import_module(f"{env}.utils.eo_operators")
default_args = {
    "owner": "airflow",
    "depends_on_past": False,
    "start_date": datetime(2024, 3, 23),
    "email_on_failure": False,
    "email_on_retry": False,
    "retries": 1,
}

with DAG(
    utils.get_dag_name(__file__, "cma"),
    default_args=default_args,
    description=(
        "A pipeline to fetch, process, and load to validate data into postgresql"
        " for CMA reparacteur dataset"
    ),
    params={
        "endpoint": (
            "https://data.artisanat.fr/api/explore/v2.1/catalog/datasets/reparacteurs/records"
        ),
        "reparacteurs": True,
        "column_mapping": {
            "name": "nom",
            "reparactor_description": "description",
            "address_1": "adresse",
            "address_2": "adresse_complement",
            "zip_code": "code_postal",
            "zip_code_label": "ville",
            "website": "url",
            "email": "email",
            "phone": "telephone",
            "siret": "siret",
            "id": "identifiant_externe",
            "is_enabled": "statut",
            "other_info": "commentaires",
            "creation_date": "cree_le",
            "update_date": "modifie_le",
            "reparactor_hours": "horaires_description",
        },
        "mapping_config_key": "sous_categories_cma",
    },
    schedule=None,
) as dag:
    (
        [
            eo_operators.fetch_data_from_api_task(dag),
            eo_operators.load_data_from_postgresql_task(dag),
        ]
        >> eo_operators.create_actors_task(dag)
        >> [
            eo_operators.create_proposition_services_task(dag),
            eo_operators.create_labels_task(dag),
            eo_operators.create_acteur_services_task(dag),
        ]
        >> eo_operators.create_proposition_services_sous_categories_task(dag)
        >> eo_operators.serialize_to_json_task(dag)
        >> eo_operators.write_data_task(dag)
    )  # type: ignore
