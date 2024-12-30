from airflow import DAG
from sources.config import shared_constants as constants
from sources.config.airflow_params import get_mapping_config
from sources.tasks.airflow_logic.operators import default_args, eo_task_chain

with DAG(
    dag_id="eo-pyreo",
    dag_display_name="Source - PYREO",
    default_args=default_args,
    description=(
        "A pipeline to fetch, process, and load to validate data into postgresql"
        " for Pyreo dataset"
    ),
    params={
        "column_transformations": [
            # 1. Renommage des colonnes
            {
                "origin": "id_point_apport_ou_reparation",
                "destination": "identifiant_externe",
            },
            {
                "origin": "ecoorganisme",
                "destination": "source_id",
            },
            {
                "origin": "nom_de_lorganisme",
                "destination": "nom",
            },
            {
                "origin": "longitudewgs84",
                "destination": "longitude",
            },
            {
                "origin": "latitudewgs84",
                "destination": "latitude",
            },
            # 2. Transformation des colonnes
            {
                "origin": "type_de_point_de_collecte",
                "transformation": "clean_acteur_type_code",
                "destination": "acteur_type_code",
            },
            # 3. Ajout des colonnes avec une valeur par défaut
            {
                "column": "type_de_point_de_collecte",
                "value": (
                    "magasin / franchise, enseigne commerciale / distributeur /"
                    " point de vente"
                ),
            },
            {
                "column": "statut",
                "value": constants.ACTEUR_ACTIF,
            },
            # 4. Transformation du dataframe
            {
                "origin": ["siret"],
                "transformation": "clean_siret_and_siren",
                "destination": ["siret", "siren"],
            },
            # 5. Supression des colonnes
            {"remove": "_i"},
            {"remove": "_id"},
            {"remove": "_updatedAt"},
            {"remove": "_rand"},
            {"remove": "_geopoint"},
            {"remove": "filiere"},
            {"remove": "_score"},
            # 6. Colonnes à garder (rien à faire, utilisé pour le controle)
            {"keep": "public_accueilli"},
            {"keep": "produitsdechets_acceptes"},
            {"keep": "reprise"},
            {"keep": "point_de_collecte_ou_de_reprise_des_dechets"},
            {"keep": "adresse_format_ban"},
            {"keep": "labels_etou_bonus"},
            {"keep": "point_dapport_de_service_reparation"},
            {"keep": "point_dapport_pour_reemploi"},
            {"keep": "point_de_reparation"},
        ],
        "endpoint": (
            "https://data.pointsapport.ademe.fr/data-fair/api/v1/datasets/"
            "donnees-eo-pyreo/lines?size=10000"
        ),
        "ignore_duplicates": False,
        "validate_address_with_ban": False,
        "product_mapping": get_mapping_config(),
    },
    schedule=None,
) as dag:
    eo_task_chain(dag)
