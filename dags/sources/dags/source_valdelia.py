from airflow import DAG
from sources.config import shared_constants as constants
from sources.config.airflow_params import get_mapping_config
from sources.tasks.airflow_logic.operators import default_args, eo_task_chain

with DAG(
    dag_id="eo-valdelia",
    dag_display_name="Source - VALDELIA",
    default_args=default_args,
    description=(
        "A pipeline to fetch, process, and load to validate data into postgresql"
        " for Valdelia dataset"
    ),
    params={
        "column_transformations": [
            {
                "origin": "siren",
                "transformation": "clean_siren",
                "destination": "siren",
            },
            {
                "origin": "siret",
                "transformation": "clean_siret",
                "destination": "siret",
            },
        ],
        "column_mapping": {
            "id_point_apport_ou_reparation": "identifiant_externe",
            "type_de_point_de_collecte": "acteur_type_id",
            "exclusivite_de_reprisereparation": "exclusivite_de_reprisereparation",
            "uniquement_sur_rdv": "uniquement_sur_rdv",
            "public_accueilli": "public_accueilli",
            "reprise": "reprise",
            "siret": "siret",
            "telephone": "telephone",
            "produitsdechets_acceptes": "produitsdechets_acceptes",
            "labels_etou_bonus": "labels_etou_bonus",
            "point_de_reparation": "point_de_reparation",
            "ecoorganisme": "source_id",
            "adresse_format_ban": "adresse_format_ban",
            "nom_de_lorganisme": "nom",
            "perimetre_dintervention": "perimetre_dintervention",
            "longitudewgs84": "longitude",
            "latitudewgs84": "latitude",
        },
        "columns_to_add_by_default": {
            "statut": constants.ACTEUR_ACTIF,
        },
        "endpoint": (
            "https://data.pointsapport.ademe.fr/data-fair/api/v1/datasets/"
            "donnees-eo-valdelia/lines?size=10000"
        ),
        "ignore_duplicates": False,
        "validate_address_with_ban": False,
        "product_mapping": get_mapping_config(),
    },
    schedule=None,
) as dag:
    eo_task_chain(dag)
