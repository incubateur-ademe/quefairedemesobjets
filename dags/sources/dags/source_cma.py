from airflow import DAG
from sources.config import shared_constants as constants
from sources.config.airflow_params import get_mapping_config
from sources.tasks.airflow_logic.operators import (
    default_args,
    default_params,
    eo_task_chain,
)

with DAG(
    dag_id="cma",
    dag_display_name="Source - CMA",
    default_args=default_args,
    description=(
        "A pipeline to fetch, process, and load to validate data into postgresql"
        " for CMA reparacteur dataset"
    ),
    tags=["source", "data.artisanat.fr", "fédération", "cma", "reparacteur"],
    **default_params,
    params={
        "normalization_rules": [
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
                "origin": "website",
                "destination": "url",
            },
            {
                "origin": "adresse_2",
                "destination": "adresse_complement",
            },
            {
                "origin": "ville",
                "destination": "ville",
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
                "value": constants.ACTEUR_ACTIF,
            },
            {
                "column": "label_codes",
                "value": ["reparacteur"],
            },
            {
                "column": "acteur_type_code",
                "value": "commerce",
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
                "value": constants.PUBLIC_PAR,
            },
            {
                "column": "source_code",
                "value": "cmareparacteur",
            },
            # 4. Transformation du dataframe
            {
                "origin": ["final_latitude", "final_longitude"],
                "transformation": "compute_location",
                "destination": ["location"],
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
            {"remove": "categorie"},
            {"remove": "categorie_2"},
            {"remove": "categorie_3"},
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
            {"remove": "linkedin"},
            {"remove": "logo_file"},
            {"remove": "naf"},
            {"remove": "nom_gerant"},
            {"remove": "region"},
            {"remove": "rgpd"},
            {"remove": "techloadts"},
            {"remove": "techprocessid"},
            {"remove": "techsource"},
            {"remove": "latitude"},
            {"remove": "libelle_naf"},
            {"remove": "longitude"},
            # 6. Colonnes à garder (rien à faire, utilisé pour le controle)
            {"keep": "nom"},
            {"keep": "adresse"},
            {"keep": "description"},
            {"keep": "email"},
            {"keep": "ville"},
        ],
        "endpoint": ("https://apiopendata.artisanat.fr/reparacteur"),
        "validate_address_with_ban": False,
        "product_mapping": get_mapping_config(mapping_key="sous_categories_cma"),
    },
) as dag:
    eo_task_chain(dag)
