import json

from airflow import DAG
from airflow.models.param import Param
from airflow.sdk.definitions.param import ParamsDict
from shared.config.airflow import DEFAULT_ARGS
from shared.config.tags import TAGS
from sources.config.airflow_params import get_souscategorie_mapping_from_db
from sources.tasks.airflow_logic.operators import default_params, eo_task_chain

with DAG(
    dag_id="source-s3",
    dag_display_name="Source - DEPUIS S3",
    default_args=DEFAULT_ARGS,
    description=(
        "Un pipeline pour récupérer des données depuis un bucket S3 et les transformer"
    ),
    tags=[TAGS.SOURCE, TAGS.S3],
    **default_params,
    params=ParamsDict(
        {
            "s3_connection_id": Param(
                "s3data",
                type="string",
                description="ID de la connexion S3 à utiliser",
            ),
            "endpoint": Param(
                "s3://lvao-data-source/unique/unique_20250310.xlsx",
                type="string",
                description="Remplacer par l'URL S3 du fichier à récupérer",
            ),
            "normalization_rules": json.dumps(
                [
                    # 1. Renommage des colonnes
                    # 2. Transformation des colonnes
                    {
                        "origin": "sous_categorie_codes",
                        "transformation": "clean_sous_categorie_codes",
                        "destination": "sous_categorie_codes",
                    },
                    {
                        "origin": "nom",
                        "transformation": "strip_string",
                        "destination": "nom",
                    },
                    {
                        "origin": "nom_commercial",
                        "transformation": "strip_string",
                        "destination": "nom_commercial",
                    },
                    {
                        "origin": "nom_officiel",
                        "transformation": "strip_string",
                        "destination": "nom_officiel",
                    },
                    {
                        "origin": "source_code",
                        "transformation": "strip_lower_string",
                        "destination": "source_code",
                    },
                    {
                        "origin": "acteur_service_codes",
                        "transformation": "clean_code_list",
                        "destination": "acteur_service_codes",
                    },
                    {
                        "origin": "action_codes",
                        "transformation": "clean_code_list",
                        "destination": "action_codes",
                    },
                    {
                        "origin": "code_postal",
                        "transformation": "clean_code_postal",
                        "destination": "code_postal",
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
                        "origin": "adresse",
                        "transformation": "strip_string",
                        "destination": "adresse",
                    },
                    {
                        "origin": "adresse_complement",
                        "transformation": "strip_string",
                        "destination": "adresse_complement",
                    },
                    {
                        "origin": "ville",
                        "transformation": "strip_string",
                        "destination": "ville",
                    },
                    {
                        "origin": "identifiant_externe",
                        "transformation": "strip_string",
                        "destination": "identifiant_externe",
                    },
                    # 3. Ajout des colonnes avec une valeur par défaut
                    # 4. Transformation du dataframe
                    {
                        "origin": ["label_codes", "acteur_type_code"],
                        "transformation": "clean_label_codes",
                        "destination": ["label_codes"],
                    },
                    {
                        "origin": ["latitude", "longitude"],
                        "transformation": "compute_location",
                        "destination": ["location", "latitude", "longitude"],
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
                        "origin": ["siret", "siren"],
                        "transformation": "clean_siret_and_siren",
                        "destination": ["siret", "siren"],
                    },
                    {
                        "origin": ["telephone", "code_postal"],
                        "transformation": "clean_telephone",
                        "destination": ["telephone"],
                    },
                    {
                        "origin": ["action_codes", "sous_categorie_codes"],
                        "transformation": "clean_proposition_services",
                        "destination": ["proposition_service_codes"],
                    },
                    # 5. Supression des colonnes
                    # 6. Colonnes à garder (rien à faire, utilisé pour le controle)
                    {"keep": "acteur_type_code"},
                    {"keep": "commentaires"},
                    {"keep": "description"},
                    {"keep": "horaires_description"},
                    {"keep": "horaires_osm"},
                    {"keep": "identifiant_externe"},
                    {"keep": "latitude"},
                    {"keep": "longitude"},
                    {"keep": "naf_principal"},
                    {"keep": "statut"},
                    {"keep": "url"},
                ]
            ),
            "validate_address_with_ban": False,
            "product_mapping": get_souscategorie_mapping_from_db(),
            "use_legacy_suggestions": True,
        }
    ),
) as dag:
    eo_task_chain(dag)
