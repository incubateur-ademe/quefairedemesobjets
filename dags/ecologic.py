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
    utils.get_dag_name(__file__, "ecologic"),
    default_args=default_args,
    description=(
        "A pipeline to fetch, process, and load to validate data into postgresql"
        " for Ecologic dataset"
    ),
    params={
        "endpoint": (
            "https://data.pointsapport.ademe.fr/data-fair/api/v1/datasets/"
            "donnees-eo-ecologic/lines?size=10000"
        ),
        "column_mapping": {
            "id_point_apport_ou_reparation": "identifiant_externe",
            "type_de_point_de_collecte": "acteur_type_id",
            "uniquement_sur_rdv": "",
            "exclusivite_de_reprisereparation": "exclusivite_de_reprisereparation",
            "filiere": "",
            "public_accueilli": "",
            "produitsdechets_acceptes": "",
            "labels_etou_bonus": "",
            "reprise": "",
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
            eo_operators.fetch_data_task(dag),
            eo_operators.load_data_task(dag),
        ]
        >> eo_operators.create_actors_task(dag)
        >> [
            eo_operators.create_proposition_services_task(dag),
            eo_operators.create_labels_task(dag),
        ]
        >> eo_operators.create_proposition_services_sous_categories_task(dag)
        >> eo_operators.serialize_to_json_task(dag)
        >> eo_operators.write_data_task(dag)
    )  # type: ignore
