from airflow import DAG
from sources.config import shared_constants as constants
from sources.config.airflow_params import get_mapping_config
from sources.tasks.airflow_logic.operators import default_args, eo_task_chain

with DAG(
    dag_id="like-eo-from-api-cma",
    dag_display_name="Source - CMA",
    default_args=default_args,
    description=(
        "A pipeline to fetch, process, and load to validate data into postgresql"
        " for CMA reparacteur dataset"
    ),
    params={
        "column_transformations": [
            {
                "origin": "siret",
                "transformation": "clean_siret",
                "destination": "siret",
            },
        ],
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
            "longitude": "longitude",
            "latitude": "latitude",
            "id": "identifiant_externe",
            "is_enabled": "statut",
            "other_info": "commentaires",
            "update_date": "modifie_le",
            "reparactor_hours": "horaires_description",
        },
        "columns_to_add_by_default": {
            "statut": constants.ACTEUR_ACTIF,
            "labels_etou_bonus": "reparacteur",
            "acteur_type_id": "artisan, commerce indépendant",
            "point_de_reparation": True,
            "public_accueilli": constants.PUBLIC_PAR,
        },
        "combine_columns_categories": ["categorie", "categorie2", "categorie3"],
        "endpoint": (
            "https://data.artisanat.fr/api/explore/v2.1/catalog/datasets/reparacteurs/records"
        ),
        "ignore_duplicates": False,
        "validate_address_with_ban": False,
        "product_mapping": get_mapping_config(mapping_key="sous_categories_cma"),
        "source_code": "cma_reparacteur",
    },
    schedule=None,
) as dag:
    eo_task_chain(dag)
