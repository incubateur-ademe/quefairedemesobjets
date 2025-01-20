from airflow import DAG
from sources.config import shared_constants as constants
from sources.config.airflow_params import get_mapping_config
from sources.tasks.airflow_logic.operators import default_args, eo_task_chain

with DAG(
    dag_id="eo-ecosystem",
    dag_display_name="Source - ECOSYSTEM",
    default_args=default_args,
    description=(
        "A pipeline to fetch, process, and load to validate data into postgresql"
        " for Ecosystem dataset"
    ),
    params={
        "normalization_rules": [
            # 1. Renommage des colonnes
            {
                "origin": "nom_de_lorganisme",
                "destination": "nom",
            },
            {
                "origin": "enseigne_commerciale",
                "destination": "nom_commercial",
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
                "origin": "ecoorganisme",
                "transformation": "strip_lower_string",
                "destination": "source_code",
            },
            {
                "origin": "type_de_point_de_collecte",
                "transformation": "clean_acteur_type_code",
                "destination": "acteur_type_code",
            },
            {
                "origin": "public_accueilli",
                "transformation": "clean_public_accueilli",
                "destination": "public_accueilli",
            },
            {
                "origin": "produitsdechets_acceptes",
                "transformation": "clean_souscategorie_codes",
                "destination": "souscategorie_codes",
            },
            # 3. Ajout des colonnes avec une valeur par défaut
            {
                "column": "statut",
                "value": constants.ACTEUR_ACTIF,
            },
            {
                "column": "label_codes",
                "value": [],
            },
            # 4. Transformation du dataframe
            {
                "origin": ["latitude", "longitude"],
                "transformation": "compute_location",
                "destination": ["location"],
            },
            {
                "origin": ["id_point_apport_ou_reparation", "nom"],
                "transformation": "clean_identifiant_externe",
                "destination": ["identifiant_externe"],
            },
            {
                "origin": [
                    "identifiant_externe",
                    "source_code",
                ],
                "transformation": "clean_identifiant_unique",
                "destination": ["identifiant_unique"],
            },
            {
                "origin": ["siren"],
                "transformation": "clean_siret_and_siren",
                "destination": ["siret", "siren"],
            },
            {
                "origin": ["adresse_format_ban"],
                "transformation": "clean_adresse",
                "destination": ["adresse", "code_postal", "ville"],
            },
            {
                "origin": [
                    "point_dapport_pour_reemploi",
                    "point_de_collecte_ou_de_reprise_des_dechets",
                ],
                "transformation": "clean_acteurservice_codes",
                "destination": ["acteurservice_codes"],
            },
            {
                "origin": [
                    "point_dapport_pour_reemploi",
                    "point_de_collecte_ou_de_reprise_des_dechets",
                ],
                "transformation": "clean_action_codes",
                "destination": ["action_codes"],
            },
            # 5. Supression des colonnes
            {"remove": "_i"},
            {"remove": "_id"},
            {"remove": "_updatedAt"},
            {"remove": "_rand"},
            {"remove": "_geopoint"},
            {"remove": "filiere"},
            {"remove": "_score"},
            {"remove": "adresse_format_ban"},
            {"remove": "id_point_apport_ou_reparation"},
            {"remove": "point_de_collecte_ou_de_reprise_des_dechets"},
            {"remove": "point_dapport_pour_reemploi"},
            {"remove": "siret"},
            # 6. Colonnes à garder (rien à faire, utilisé pour le controle)
            {"keep": "adresse_complement"},
        ],
        "endpoint": (
            "https://data.pointsapport.ademe.fr/data-fair/api/v1/datasets/"
            "donnees-eo-ecosystem/lines?size=10000"
        ),
        "ignore_duplicates": False,
        "validate_address_with_ban": False,
        "product_mapping": get_mapping_config(mapping_key="sous_categories_3eee"),
    },
    schedule=None,
) as dag:
    eo_task_chain(dag)
