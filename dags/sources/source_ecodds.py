from airflow import DAG
from utils.base_utils import get_mapping_config
from utils.eo_operators import default_args, eo_task_chain

with DAG(
    dag_id="eo-ecodds",
    dag_display_name="Source - ECODDS",
    default_args=default_args,
    description=(
        "A pipeline to fetch, process, and load to validate data into postgresql"
        " for EcoDDS dataset"
    ),
    params={
        "column_mapping": {
            "id_point_apport_ou_reparation": "identifiant_externe",
            "type_de_point_de_collecte": "acteur_type_id",
            "ecoorganisme": "source_id",
            "adresse_format_ban": "adresse_format_ban",
            "exclusivite_de_reprisereparation": "exclusivite_de_reprisereparation",
            "uniquement_sur_rdv": "uniquement_sur_rdv",
            "public_accueilli": "public_accueilli",
            "reprise": "reprise",
            "nom_de_lorganisme": "nom",
            "enseigne_commerciale": "nom_commercial",
            "longitudewgs84": "longitude",
            "latitudewgs84": "latitude",
        },
        "column_to_drop": [
            "perimetre_dintervention",
        ],
        "columns_to_add_by_default": {
            "statut": "ACTIF",
        },
        "endpoint": (
            "https://data.pointsapport.ademe.fr/data-fair/api/v1/datasets/"
            "donnees-eo-ecodds/lines?size=10000"
        ),
        "ignore_duplicates": False,
        "validate_address_with_ban": False,
        "product_mapping": get_mapping_config(),
    },
    schedule=None,
) as dag:
    eo_task_chain(dag)
