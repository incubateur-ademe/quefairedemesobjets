from airflow import DAG
from utils.base_utils import get_mapping_config
from utils.eo_operators import default_args, eo_task_chain

with DAG(
    dag_id="eo-ocad3e",
    dag_display_name="Source - OCAD3E (ECOSYSTEM & ECOLOGIC) - label QualiRépar",
    default_args=default_args,
    description=(
        "A pipeline to fetch, process, and load to validate data into postgresql"
        " for OCAD3E dataset"
    ),
    params={
        "column_mapping": {
            "id_point_apport_ou_reparation": "identifiant_externe",
            "type_de_point_de_collecte": "acteur_type_id",
            "nom_de_lorganisme": "nom",
            "enseigne_commerciale": "nom_commercial",
            "longitudewgs84": "longitude",
            "uniquement_sur_rdv": "uniquement_sur_rdv",
            "public_accueilli": "public_accueilli",
            "reprise": "reprise",
            "labels_etou_bonus": "labels_etou_bonus",
            "exclusivite_de_reprisereparation": "exclusivite_de_reprisereparation",
            "latitudewgs84": "latitude",
            "adresse_format_ban": "adresse_format_ban",
        },
        "columns_to_add_by_default": {
            "statut": "ACTIF",
        },
        "endpoint": (
            "https://data.pointsapport.ademe.fr/data-fair/api/v1/datasets/"
            "donnees-eo-ocad3e/lines?size=10000"
        ),
        "ignore_duplicates": False,
        "validate_address_with_ban": False,
        "label_bonus_reparation": "qualirepar",
        "product_mapping": get_mapping_config(mapping_key="sous_categories_qualirepar"),
        "source_code": "ocad3e",
    },
    schedule=None,
) as dag:
    eo_task_chain(dag)
