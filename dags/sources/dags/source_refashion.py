from airflow import DAG
from sources.config import shared_constants as constants
from sources.config.airflow_params import get_mapping_config
from sources.tasks.airflow_logic.operators import default_args, eo_task_chain

with DAG(
    dag_id="eo-refashion",
    dag_display_name="Source - REFASHION",
    default_args=default_args,
    description=(
        "A pipeline to fetch, process, and load to validate data into postgresql"
        " for Refashion dataset"
    ),
    params={
        "normalization_rules": [
            {
                "origin": "siret",
                "transformation": "clean_siret",
                "destination": "siret",
            },
            {
                "origin": "site_web",
                "transformation": "clean_url",
                "destination": "url",
            },
        ],
        "column_mapping": {
            "id_point_apport_ou_reparation": "identifiant_externe",
            "adresse_complement": "adresse_complement",
            "type_de_point_de_collecte": "acteur_type_id",
            "ecoorganisme": "source_id",
            "nom_de_lorganisme": "nom",
            "enseigne_commerciale": "nom_commercial",
            "site_web": "url",
            "longitudewgs84": "longitude",
            "latitudewgs84": "latitude",
            "horaires_douverture": "horaires_description",
            "consignes_dacces": "commentaires",
        },
        "columns_to_add_by_default": {
            "statut": constants.ACTEUR_ACTIF,
        },
        "endpoint": (
            "https://data.pointsapport.ademe.fr/data-fair/api/v1/datasets/"
            "donnees-eo-refashion/lines?size=10000"
        ),
        "ignore_duplicates": False,
        "validate_address_with_ban": False,
        "label_bonus_reparation": "refashion",
        "product_mapping": get_mapping_config(),
    },
    schedule=None,
) as dag:
    eo_task_chain(dag)
