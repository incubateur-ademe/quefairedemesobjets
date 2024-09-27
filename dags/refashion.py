from airflow import DAG
from utils.eo_operators import default_args, eo_task_chain

with DAG(
    dag_id="eo-refashion",
    dag_display_name="Téléchargement de la source REFASHION",
    default_args=default_args,
    description=(
        "A pipeline to fetch, process, and load to validate data into postgresql"
        " for Refashion dataset"
    ),
    params={
        "endpoint": (
            "https://data.pointsapport.ademe.fr/data-fair/api/v1/datasets/"
            "donnees-eo-refashion/lines?size=10000"
        ),
        "column_mapping": {
            "id_point_apport_ou_reparation": "identifiant_externe",
            "adresse_complement": "adresse_complement",
            "type_de_point_de_collecte": "acteur_type_id",
            "telephone": "telephone",
            "siret": "siret",
            "exclusivite_de_reprisereparation": "exclusivite_de_reprisereparation",
            "uniquement_sur_rdv": "uniquement_sur_rdv",
            "filiere": "",
            "public_accueilli": "public_accueilli",
            "produitsdechets_acceptes": "",
            "labels_etou_bonus": "",
            "reprise": "reprise",
            "point_de_reparation": "",
            "ecoorganisme": "source_id",
            "adresse_format_ban": "adresse",
            "nom_de_lorganisme": "nom",
            "enseigne_commerciale": "nom_commercial",
            "_updatedAt": "cree_le",
            "site_web": "url",
            "email": "email",
            "perimetre_dintervention": "",
            "longitudewgs84": "longitude",
            "latitudewgs84": "latitude",
            "horaires_douverture": "horaires_description",
            "consignes_dacces": "commentaires",
        },
    },
    schedule=None,
) as dag:
    eo_task_chain(dag)
