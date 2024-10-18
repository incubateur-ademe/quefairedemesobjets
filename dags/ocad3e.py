from airflow import DAG
from utils.eo_operators import default_args, eo_task_chain

with DAG(
    dag_id="eo-ocad3e",
    dag_display_name=(
        "Téléchargement de la source ECOD3E (ECOSYSTEM & ECOLOGIC) - label QualiRépar"
    ),
    default_args=default_args,
    description=(
        "A pipeline to fetch, process, and load to validate data into postgresql"
        " for ECOD3E dataset"
    ),
    params={
        "endpoint": (
            "https://data.pointsapport.ademe.fr/data-fair/api/v1/datasets/"
            "donnees-eo-ocad3e/lines?size=10000"
        ),
        "column_mapping": {
            "ecoorganisme": "source_id",
            "id_point_apport_ou_reparation": "identifiant_externe",
            "type_de_point_de_collecte": "acteur_type_id",
            "nom_de_lorganisme": "nom",
            "enseigne_commerciale": "nom_commercial",
            "labels_etou_bonus": "labels_etou_bonus",
            "longitudewgs84": "longitude",
            "latitudewgs84": "latitude",
            "adresse_format_ban": "adresse",
        },
        # TODO : lever une erreur si des colonnes sont manquantes
        "needed_columns": [
            "point_dapport_pour_reemploi",
            "point_de_reparation",
            "point_dapport_de_service_reparation",
            "point_de_collecte_ou_de_reprise_des_dechets",
            "labels_etou_bonus",
            "uniquement_sur_rdv",
            "public_accueilli",
            "reprise",
            "exclusivite_de_reprisereparation",
            "produitsdechets_acceptes",
            "adresse_complement",
            "siret",
            "siren",
            "consignes_dacces",
            "accessible" "email",
            "telephone",
            "site_web",
            "horaires_douverture",
            "service_a_domicile",
            "perimetre_dintervention",
            # "date_debut_point_ephemere",
            # "date_fin_point_ephemere",
        ],
        "label_bonus_reparation": "qualirepar",
        "mapping_config_key": "sous_categories_qualirepar",
    },
    schedule=None,
) as dag:
    eo_task_chain(dag)
