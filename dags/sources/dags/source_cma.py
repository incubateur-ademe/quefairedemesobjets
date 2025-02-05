from airflow import DAG
from sources.config import shared_constants as constants
from sources.config.airflow_params import get_mapping_config
from sources.tasks.airflow_logic.operators import default_args, eo_task_chain

with DAG(
    dag_id="cma",
    dag_display_name="Source - CMA",
    default_args=default_args,
    description=(
        "A pipeline to fetch, process, and load to validate data into postgresql"
        " for CMA reparacteur dataset"
    ),
    params={
        "normalization_rules": [
            # 1. Renommage des colonnes
            {
                "origin": "name",
                "destination": "nom",
            },
            {
                "origin": "reparactor_description",
                "destination": "description",
            },
            {
                "origin": "address_1",
                "destination": "adresse",
            },
            {
                "origin": "address_2",
                "destination": "adresse_complement",
            },
            {
                "origin": "zip_code_label",
                "destination": "ville",
            },
            {
                "origin": "website",
                "destination": "url",
            },
            {
                "origin": "id",
                "destination": "identifiant_externe",
            },
            {
                "origin": "other_info",
                "destination": "commentaires",
            },
            {
                "origin": "update_date",
                "destination": "modifie_le",
            },
            {
                "origin": "reparactor_hours",
                "destination": "horaires_description",
            },
            {
                "origin": "phone",
                "destination": "telephone",
            },
            # 2. Transformation des colonnes
            {
                "origin": "zip_code",
                "transformation": "clean_code_postal",
                "destination": "code_postal",
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
                "column": "acteurservice_codes",
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
                "transformation": "clean_id",
                "destination": ["id"],
            },
            {
                "origin": ["siret"],
                "transformation": "clean_siret_and_siren",
                "destination": ["siret", "siren"],
            },
            {
                "origin": ["categorie", "categorie2", "categorie3"],
                "transformation": "merge_and_clean_souscategorie_codes",
                "destination": ["souscategorie_codes"],
            },
            {
                "origin": ["action_codes", "souscategorie_codes"],
                "transformation": "clean_proposition_services",
                "destination": ["proposition_services_codes"],
            },
            # 5. Supression des colonnes
            {"remove": "activite"},
            {"remove": "ban_adresse"},
            {"remove": "ban_code_postal"},
            {"remove": "ban_latitude"},
            {"remove": "ban_longitude"},
            {"remove": "ban_ville"},
            {"remove": "categorie"},
            {"remove": "categorie2"},
            {"remove": "categorie3"},
            {"remove": "cma_code"},
            {"remove": "code_nafa"},
            {"remove": "creation_date"},
            {"remove": "departement"},
            {"remove": "final_latitude"},
            {"remove": "final_longitude"},
            {"remove": "geocode"},
            {"remove": "geocoding_status"},
            {"remove": "is_enabled"},
            {"remove": "is_error"},
            {"remove": "is_reparactor"},
            {"remove": "is_updated"},
            {"remove": "likes"},
            {"remove": "logo_file"},
            {"remove": "org_cnt_facebook"},
            {"remove": "org_cnt_instagram"},
            {"remove": "org_cnt_linkedin"},
            {"remove": "region"},
            {"remove": "reparactor_certificates"},
            {"remove": "reparactor_services"},
            {"remove": "source"},
            # 6. Colonnes à garder (rien à faire, utilisé pour le controle)
            {"keep": "email"},
            {"keep": "longitude"},
            {"keep": "latitude"},
        ],
        "endpoint": (
            "https://data.artisanat.fr/api/explore/v2.1/catalog/datasets/reparacteurs/records"
        ),
        "ignore_duplicates": False,
        "validate_address_with_ban": False,
        "product_mapping": get_mapping_config(mapping_key="sous_categories_cma"),
    },
    schedule=None,
) as dag:
    eo_task_chain(dag)
