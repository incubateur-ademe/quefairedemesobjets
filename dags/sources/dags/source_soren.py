from airflow import DAG
from sources.config.airflow_params import get_mapping_config
from sources.tasks.airflow_logic.operators import default_args, eo_task_chain

with DAG(
    dag_id="eo-soren",
    dag_display_name="Source - SOREN",
    default_args=default_args,
    description=(
        "A pipeline to fetch, process, and load to validate data into postgresql"
        " for Soren dataset"
    ),
    params={
        "column_transformations": [
            {
                "origin": "horaires_douverture",
                "transformation": "convert_opening_hours",
                "destination": "horaires_description",
            }
        ],
        "column_mapping": {
            "id_point_apport_ou_reparation": "identifiant_externe",
            "type_de_point_de_collecte": "acteur_type_id",
            "exclusivite_de_reprisereparation": "exclusivite_de_reprisereparation",
            "uniquement_sur_rdv": "uniquement_sur_rdv",
            "public_accueilli": "public_accueilli",
            "reprise": "reprise",
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
            "statut": "ACTIF",
        },
        "endpoint": (
            "https://data.pointsapport.ademe.fr/data-fair/api/v1/datasets/"
            "donnees-eo-soren/lines?size=10000"
        ),
        "ignore_duplicates": False,
        "validate_address_with_ban": False,
        "product_mapping": get_mapping_config(),
    },
    schedule=None,
) as dag:
    eo_task_chain(dag)
