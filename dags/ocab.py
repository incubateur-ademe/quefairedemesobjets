from datetime import datetime

import utils.eo_operators as eo_operators
from airflow import DAG

default_args = {
    "owner": "airflow",
    "depends_on_past": False,
    "start_date": datetime(2024, 3, 23),
    "email_on_failure": False,
    "email_on_retry": False,
    "retries": 1,
}

with DAG(
    "eo-ocab",
    default_args=default_args,
    description=(
        "A pipeline to fetch, process, and load to validate data into postgresql"
        " for OCAB dataset"
    ),
    params={
        "endpoint": (
            "https://data.pointsapport.ademe.fr/data-fair/api/v1/datasets/"
            "donnees-eo-ocab/lines?size=10000"
        ),
        "column_mapping": {
            "id_point_apport_ou_reparation": "identifiant_externe",
            "type_de_point_de_collecte": "acteur_type_id",
            "exclusivite_de_reprisereparation": "exclusivite_de_reprisereparation",
            "uniquement_sur_rdv": "uniquement_sur_rdv",
            "public_accueilli": "public_accueilli",
            "reprise": "reprise",
            "filiere": "",
            "siret": "siret",
            "produitsdechets_acceptes": "",
            "labels_etou_bonus": "",
            "point_de_reparation": "",
            "ecoorganisme": "source_id",
            "adresse_format_ban": "adresse",
            "nom_de_lorganisme": "nom",
            "_updatedAt": "cree_le",
            "perimetre_dintervention": "",
            "longitudewgs84": "location",
            "latitudewgs84": "location",
        },
    },
    schedule=None,
) as dag:
    (
        [
            eo_operators.fetch_data_from_api_task(dag),
            eo_operators.load_data_from_postgresql_task(dag),
        ]
        >> eo_operators.create_actors_task(dag)
        >> [
            eo_operators.create_proposition_services_task(dag),
            eo_operators.create_labels_task(dag),
            eo_operators.create_acteur_services_task(dag),
        ]
        >> eo_operators.create_proposition_services_sous_categories_task(dag)
        >> eo_operators.serialize_to_json_task(dag)
        >> eo_operators.write_data_task(dag)
    )  # type: ignore
