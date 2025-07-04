from airflow import DAG
from shared.config.tags import TAGS
from sources.config import shared_constants as constants
from sources.config.airflow_params import get_mapping_config
from sources.tasks.airflow_logic.operators import (
    default_args,
    default_params,
    eo_task_chain,
)

with DAG(
    dag_id="eo-soren",
    dag_display_name="Source - SOREN",
    default_args=default_args,
    description=(
        "A pipeline to fetch, process, and load to validate data into postgresql"
        " for Soren dataset"
    ),
    tags=[
        TAGS.SOURCE,
        TAGS.DATA_POINTSAPPORT_ADEME,
        TAGS.ECO_ORGANISME,
        TAGS.SOREN,
        TAGS.EEE,
    ],
    **default_params,
    params={
        "normalization_rules": [
            # 1. Renommage des colonnes
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
                "origin": "ecoorganisme",
                "transformation": "strip_lower_string",
                "destination": "source_code",
            },
            {
                "origin": "horaires_douverture",
                "transformation": "clean_horaires_osm",
                "destination": "horaires_osm",
            },
            {
                "origin": "horaires_osm",
                "transformation": "convert_opening_hours",
                "destination": "horaires_description",
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
                "origin": "uniquement_sur_rdv",
                "transformation": "cast_eo_boolean_or_string_to_boolean",
                "destination": "uniquement_sur_rdv",
            },
            {
                "origin": "exclusivite_de_reprisereparation",
                "transformation": "cast_eo_boolean_or_string_to_boolean",
                "destination": "exclusivite_de_reprisereparation",
            },
            {
                "origin": "reprise",
                "transformation": "clean_reprise",
                "destination": "reprise",
            },
            {
                "origin": "produitsdechets_acceptes",
                "transformation": "clean_sous_categorie_codes",
                "destination": "sous_categorie_codes",
            },
            # 3. Ajout des colonnes avec une valeur par défaut
            {
                "column": "statut",
                "value": constants.ACTEUR_ACTIF,
            },
            # 4. Transformation du dataframe
            {
                "origin": ["siret", "siren"],
                "transformation": "clean_siret_and_siren",
                "destination": ["siret", "siren"],
            },
            {
                "origin": ["latitude", "longitude"],
                "transformation": "compute_location",
                "destination": ["location"],
            },
            {
                "origin": ["labels_etou_bonus", "acteur_type_code"],
                "transformation": "clean_label_codes",
                "destination": ["label_codes"],
            },
            {
                "origin": ["id_point_apport_ou_reparation", "nom", "acteur_type_code"],
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
                "origin": ["adresse_format_ban"],
                "transformation": "clean_adresse",
                "destination": ["adresse", "code_postal", "ville"],
            },
            {
                "origin": ["telephone", "code_postal"],
                "transformation": "clean_telephone",
                "destination": ["telephone"],
            },
            {
                "origin": [
                    "point_de_collecte_ou_de_reprise_des_dechets",
                ],
                "transformation": "clean_acteur_service_codes",
                "destination": ["acteur_service_codes"],
            },
            {
                "origin": [
                    "point_de_collecte_ou_de_reprise_des_dechets",
                ],
                "transformation": "clean_action_codes",
                "destination": ["action_codes"],
            },
            {
                "origin": ["action_codes", "sous_categorie_codes"],
                "transformation": "clean_proposition_services",
                "destination": ["proposition_service_codes"],
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
            {"remove": "labels_etou_bonus"},
            {"remove": "point_dapport_de_service_reparation"},
            {"remove": "point_dapport_pour_reemploi"},
            {"remove": "point_de_reparation"},
            {"remove": "perimetre_dintervention"},
            {"remove": "service_a_domicile"},
            # 6. Colonnes à garder (rien à faire, utilisé pour le controle)
            {"keep": "email"},
        ],
        "endpoint": (
            "https://data.pointsapport.ademe.fr/data-fair/api/v1/datasets/"
            "donnees-eo-soren/lines?size=10000"
        ),
        "validate_address_with_ban": False,
        "product_mapping": get_mapping_config(),
    },
) as dag:
    eo_task_chain(dag)
