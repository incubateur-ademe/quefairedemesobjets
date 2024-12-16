from airflow import DAG
from sources.config.airflow_params import get_mapping_config
from sources.tasks.airflow_logic.operators import default_args, eo_task_chain

with DAG(
    dag_id="eo-screlec",
    dag_display_name="Source - SCRELEC",
    default_args=default_args,
    description=(
        "DAG pour télécharger, standardiser, et charger dans notre base la source SINOE"
    ),
    tags=["source", "ademe", "screlec", "piles", "batteries", "accumulateurs"],
    params={
        "endpoint": (
            "https://data.ademe.fr/data-fair/api/v1/datasets/"
            "donnees-eo-screlec/lines?size=10000"
        ),
        "source_code": "SCRELEC",
        "column_transformations": [
            {
                "origin": "siret",
                "transformation": "clean_siret",
                "destination": "siret",
            },
        ],
        "column_mapping": {
            # ----------------------------------------
            # Champs à mapper
            # ----------------------------------------
            "ecoorganisme": "source_id",
            "enseigne_commerciale": "nom_commercial",
            "id_point_apport_ou_reparation": "identifiant_externe",
            "latitudewgs84": "latitude",
            "longitudewgs84": "longitude",
            "nom_de_lorganisme": "nom",
            "type_de_point_de_collecte": "acteur_type_id",
        },
        "column_to_drop": [
            "_geopoint",
            "_i",
            "_id",
            "_rand",
            "_score",
            "_updatedAt",
            "filiere",
            "accessible",
        ],
        "ignore_duplicates": False,
        "validate_address_with_ban": False,
        "product_mapping": get_mapping_config("sous_categories"),
    },
    schedule=None,
) as dag:
    eo_task_chain(dag)
