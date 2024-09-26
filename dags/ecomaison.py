from datetime import datetime
from importlib import import_module
from pathlib import Path

from airflow import DAG

env = Path(__file__).parent.name
utils = import_module(f"{env}.utils.utils")
eo_operators = import_module(f"{env}.utils.eo_operators")

default_args = {
    "owner": "airflow",
    "depends_on_past": False,
    "start_date": datetime(2024, 3, 23),
    "email_on_failure": False,
    "email_on_retry": False,
    "retries": 1,
}

with DAG(
    utils.get_dag_name(__file__, "ecomaison"),
    default_args=default_args,
    description=(
        "A pipeline to fetch, process, and load to validate data into postgresql"
        " for Ecomaison dataset"
    ),
    params={
        "endpoint": (
            "https://data.pointsapport.ademe.fr/data-fair/api/v1/datasets/"
            "donnees-eo-ecomaison/lines?size=10000"
        ),
        "multi_ecoorganisme": True,
        "column_mapping": {
            "id_point_apport_ou_reparation": "identifiant_externe",
            "type_de_point_de_collecte": "acteur_type_id",
            "exclusivite_de_reprisereparation": "exclusivite_de_reprisereparation",
            "uniquement_sur_rdv": "uniquement_sur_rdv",
            "public_accueilli": "public_accueilli",
            "reprise": "reprise",
            "filiere": "",
            "enseigne_commerciale": "nom_commercial",
            "telephone": "telephone",
            "email": "email",
            "siret": "siret",
            "produitsdechets_acceptes": "",
            "labels_etou_bonus": "",
            "point_de_reparation": "",
            "ecoorganisme": "source_id",
            "site_web": "url",
            "adresse_format_ban": "adresse",
            "nom_de_lorganisme": "nom",
            "_updatedAt": "cree_le",
            "perimetre_dintervention": "",
            "longitudewgs84": "longitude",
            "latitudewgs84": "latitude",
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
