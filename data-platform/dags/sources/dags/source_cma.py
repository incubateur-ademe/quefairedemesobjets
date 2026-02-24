import json

from airflow import DAG
from airflow.sdk.definitions.param import ParamsDict
from shared.config.airflow import DEFAULT_ARGS
from shared.config.tags import TAGS
from sources.config.airflow_params import get_mapping_config
from sources.tasks.airflow_logic.operators import default_params, eo_task_chain

from qfdmo.models.acteur import ActeurPublicAccueilli, ActeurStatus

with DAG(
    dag_id="cma",
    dag_display_name="Source - CMA",
    default_args=DEFAULT_ARGS,
    description=(
        "A pipeline to fetch, process, and load to validate data into postgresql"
        " for CMA reparacteur dataset"
    ),
    tags=[
        TAGS.SOURCE,
        TAGS.DATA_POINTSAPPORT_ADEME,
        TAGS.FEDERATION,
        TAGS.CMA,
        TAGS.REPARACTEUR,
    ],
    **default_params,
    params=ParamsDict(
        {
            "normalization_rules": json.dumps(
                [
                    # 1. Renommage des colonnes
                    {
                        "origin": "horaires",
                        "destination": "horaires_description",
                    },
                    {
                        "origin": "id",
                        "destination": "identifiant_externe",
                    },
                    {
                        "origin": "nafa",
                        "destination": "naf_principal",
                    },
                    {
                        "origin": "adresse_2",
                        "destination": "adresse_complement",
                    },
                    {
                        "origin": "final_latitude",
                        "destination": "latitude",
                    },
                    {
                        "origin": "final_longitude",
                        "destination": "longitude",
                    },
                    # 2. Transformation des colonnes
                    {
                        "origin": "code_postal",
                        "transformation": "clean_code_postal",
                        "destination": "code_postal",
                    },
                    {
                        "origin": "categories",
                        "transformation": "clean_sous_categorie_codes",
                        "destination": "sous_categorie_codes",
                    },
                    # 3. Ajout des colonnes avec une valeur par défaut
                    {
                        "column": "statut",
                        "value": ActeurStatus.ACTIF,
                    },
                    {
                        "column": "label_codes",
                        "value": ["reparacteur"],
                    },
                    {
                        "column": "acteur_type_code",
                        "value": "artisan",
                    },
                    {
                        "column": "acteur_service_codes",
                        "value": ["service_de_reparation"],
                    },
                    {
                        "column": "action_codes",
                        "value": ["reparer"],
                    },
                    {
                        "column": "public_accueilli",
                        "value": ActeurPublicAccueilli.PARTICULIERS,
                    },
                    {
                        "column": "source_code",
                        "value": "cma_reparacteur",
                    },
                    # 4. Transformation du dataframe
                    {
                        "origin": ["website", "facebook", "instagram"],
                        "transformation": "clean_url_from_multi_columns",
                        "destination": ["url"],
                    },
                    {
                        "origin": ["latitude", "longitude"],
                        "transformation": "compute_location",
                        "destination": ["location", "latitude", "longitude"],
                    },
                    {
                        "origin": ["siret"],
                        "transformation": "clean_siret_and_siren",
                        "destination": ["siret", "siren"],
                    },
                    {
                        "origin": ["telephone", "code_postal"],
                        "transformation": "clean_telephone",
                        "destination": ["telephone"],
                    },
                    {
                        "origin": ["identifiant_externe", "nom"],
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
                        "origin": ["action_codes", "sous_categorie_codes"],
                        "transformation": "clean_proposition_services",
                        "destination": ["proposition_service_codes"],
                    },
                    # 5. Supression des colonnes
                    {"remove": "activite"},
                    {"remove": "activites_detaillees"},
                    {"remove": "ban_latitude"},
                    {"remove": "ban_longitude"},
                    {"remove": "categorie_2"},
                    {"remove": "categorie_3"},
                    {"remove": "categorie"},
                    {"remove": "cma_code"},
                    {"remove": "code_departement"},
                    {"remove": "code_region"},
                    {"remove": "cog"},
                    {"remove": "date_creation_entreprise"},
                    {"remove": "departement"},
                    {"remove": "eco_maison"},
                    {"remove": "effectif"},
                    {"remove": "facebook"},
                    {"remove": "final_latitude"},
                    {"remove": "final_longitude"},
                    {"remove": "geocode"},
                    {"remove": "instagram"},
                    {"remove": "libelle_naf"},
                    {"remove": "linkedin"},
                    {"remove": "logo_file"},
                    {"remove": "naf"},
                    {"remove": "nom_gerant"},
                    {"remove": "region"},
                    {"remove": "rgpd"},
                    {"remove": "techloadts"},
                    {"remove": "techprocessid"},
                    {"remove": "techsource"},
                    {"remove": "website"},
                    # 6. Colonnes à garder (rien à faire, utilisé pour le controle)
                    {"keep": "nom"},
                    {"keep": "adresse"},
                    {"keep": "description"},
                    {"keep": "email"},
                    {"keep": "ville"},
                ]
            ),
            "endpoint": ("https://apiopendata.artisanat.fr/reparacteur"),
            "validate_address_with_ban": False,
            "product_mapping": get_mapping_config(mapping_key="sous_categories_cma"),
            "use_legacy_suggestions": True,
        }
    ),
) as dag:
    eo_task_chain(dag)
