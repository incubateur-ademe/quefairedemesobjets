from airflow import DAG
from utils.eo_operators import default_args, eo_task_chain

with DAG(
    dag_id="eo-aliapur",
    dag_display_name="Téléchargement de la source ALIAPUR",
    default_args=default_args,
    description=(
        "A pipeline to fetch, process, and load to validate data into postgresql"
        " for Aliapur dataset"
    ),
    params={
        "endpoint": (
            "https://data.pointsapport.ademe.fr/data-fair/api/v1/datasets/"
            "donnees-eo-aliapur/lines?size=10000"
        ),
        "column_mapping": {
            "id_point_apport_ou_reparation": "identifiant_externe",
            "type_de_point_de_collecte": "acteur_type_id",
            "exclusivite_de_reprisereparation": "exclusivite_de_reprisereparation",
            "uniquement_sur_rdv": "uniquement_sur_rdv",
            "public_accueilli": "public_accueilli",
            "reprise": "reprise",
            "produitsdechets_acceptes": "",
            "labels_etou_bonus": "",
            "point_de_reparation": "",
            "ecoorganisme": "source_id",
            "adresse_format_ban": "adresse",
            "nom_de_lorganisme": "nom",
            "perimetre_dintervention": "",
            "longitudewgs84": "longitude",
            "latitudewgs84": "latitude",
        },
    },
    schedule=None,
) as dag:
    eo_task_chain(dag)
