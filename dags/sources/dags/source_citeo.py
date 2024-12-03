from airflow import DAG
from sources.config.airflow_params import get_mapping_config
from sources.tasks.airflow_logic.operators import default_args, eo_task_chain

with DAG(
    dag_id="eo-citeo",
    dag_display_name="Source - CITEO",
    default_args=default_args,
    description=(
        "Injestion des données de l'éco-organisme CITEO à partir des données disponible"
        " sur de Koumoul"
    ),
    params={
        "column_transformations": [
            {
                "origin": "siren",
                "transformation": "clean_siren",
                "destination": "siren",
            },
        ],
        "column_mapping": {
            "id_point_apport_ou_reparation": "identifiant_externe",
            "type_de_point_de_collecte": "acteur_type_id",
            "ecoorganisme": "source_id",
            "nom_de_lorganisme": "nom",
            "longitudewgs84": "longitude",
            "latitudewgs84": "latitude",
        },
        "columns_to_add_by_default": {
            "statut": "ACTIF",
        },
        "endpoint": (
            "https://data.pointsapport.ademe.fr/data-fair/api/v1/datasets/"
            "donnees-eo-citeo/lines?size=10000"
        ),
        "ignore_duplicates": False,
        "validate_address_with_ban": False,
        "product_mapping": get_mapping_config(),
    },
    schedule=None,
) as dag:
    eo_task_chain(dag)
