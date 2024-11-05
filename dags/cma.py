from airflow import DAG
from utils.eo_operators import default_args, eo_task_chain

with DAG(
    dag_id="like-eo-from-api-cma",
    dag_display_name="Téléchargement de la source CMA",
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
        "source_code": "CMA - Chambre des métiers et de l'artisanat",
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
        "mapping_config_key": "sous_categories_cma",
    },
    schedule=None,
) as dag:
    eo_task_chain(dag)
