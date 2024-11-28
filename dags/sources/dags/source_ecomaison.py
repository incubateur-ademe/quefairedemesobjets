from airflow import DAG
from sources.config import shared_constants as constants
from sources.config.airflow_params import get_mapping_config
from sources.tasks.airflow_logic.operators import default_args, eo_task_chain

with DAG(
    dag_id="eo-ecomaison",
    dag_display_name="Source - ECOMAISON",
    default_args=default_args,
    description=(
        "A pipeline to fetch, process, and load to validate data into postgresql"
        " for Ecomaison dataset"
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
            "id_point_apport_ou_reparation": "identifiant_externe",
            "type_de_point_de_collecte": "acteur_type_id",
            "enseigne_commerciale": "nom_commercial",
            "ecoorganisme": "source_id",
            "site_web": "url",
            "nom_de_lorganisme": "nom",
            "longitudewgs84": "longitude",
            "latitudewgs84": "latitude",
        },
        "columns_to_add_by_default": {
            "statut": constants.ACTEUR_ACTIF,
        },
        "endpoint": (
            "https://data.pointsapport.ademe.fr/data-fair/api/v1/datasets/"
            "donnees-eo-ecomaison/lines?size=10000"
        ),
        "ignore_duplicates": False,
        "validate_address_with_ban": False,
        "merge_duplicated_acteurs": True,
        "product_mapping": get_mapping_config(),
    },
    schedule=None,
) as dag:
    eo_task_chain(dag)
