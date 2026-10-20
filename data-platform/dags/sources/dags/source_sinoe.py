from airflow import DAG
from shared.config.airflow import DEFAULT_ARGS_NO_RETRIES
from shared.config.tags import TAGS
from sources.config.airflow_params import (
    get_mapping_config,
    source_sinoe_dechet_mapping_get,
)
from sources.config.models import SinoeSourceAirflowConfig
from sources.tasks.airflow_logic.operators import default_params, eo_task_chain

SINOE_NORMALIZATION_RULES = [
    # 1. Renommage des colonnes
    {
        "origin": "code_service",
        "destination": "identifiant_externe",
    },
    {
        "origin": "libelle_service",
        "destination": "nom",
    },
    # 2. Transformation des colonnes
    {
        "origin": "code_type_dechet_admis",
        "transformation": "clean_sous_categorie_codes_sinoe",
        "destination": "sous_categorie_codes",
    },
    # 3. Ajout des colonnes avec une valeur par défaut
    {
        "column": "acteur_type_code",
        "value": "decheterie",
    },
    {
        "column": "label_codes",
        "value": [],
    },
    {
        "column": "acteur_service_codes",
        "value": ["structure_de_collecte"],
    },
    {
        "column": "action_codes",
        "value": ["trier"],
    },
    {
        "column": "source_code",
        "value": "ademesinoedecheteries",
    },
    {
        "column": "statut",
        "value": "ACTIF",
    },
    # 4. Transformation du dataframe
    {
        "origin": ["latitude", "longitude"],
        "transformation": "compute_location",
        "destination": ["location", "latitude", "longitude"],
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
    {"remove": "_geopoint"},
    {"remove": "_i"},
    {"remove": "_id"},
    {"remove": "_rand"},
    {"remove": "_score"},
    {"remove": "annee"},
    {"remove": "code_acteur_exploitant"},
    {"remove": "code_acteur_moa"},
    {"remove": "code_departement"},
    {"remove": "code_mode_gestion"},
    {"remove": "code_region"},
    {"remove": "code_service"},
    {"remove": "code_valideur"},
    {"remove": "date_ouverture_service"},
    {"remove": "libelle_acteur_exploitant"},
    {"remove": "libelle_acteur_moa"},
    {"remove": "libelle_departement"},
    {"remove": "libelle_mode_gestion"},
    {"remove": "libelle_region"},
    {"remove": "libelle_type_service"},
    {"remove": "origine"},
    {"remove": "qualite_coordonnees"},
    {"remove": "gps_adresse"},
    {"remove": "code_type_service"},
    {"remove": "date_fermeture_service"},
]

with DAG(
    dag_id="source_sinoe",
    dag_display_name="Source - SINOE",
    default_args=DEFAULT_ARGS_NO_RETRIES,
    description=(
        "DAG pour télécharger, standardiser, et charger dans notre base la source SINOE"
    ),
    tags=[
        TAGS.SOURCE,
        TAGS.DATA_ADEME,
        TAGS.ADEME,
        TAGS.SINOE,
        TAGS.DECHETTERIE,
    ],
    **default_params,
    params=SinoeSourceAirflowConfig(
        endpoint=(
            "https://data.sinoe-dechets.ademe.fr/data-fair/api/v1/datasets/"
            "liste-des-services-de-decheteries-donnees-publiques/lines"
            "?size=10000&q_mode=simple"
        ),
        metadata_endpoint=(
            "https://data.sinoe-dechets.ademe.fr/data-fair/api/v1/datasets/"
            "liste-des-services-de-decheteries-donnees-publiques/schema"
        ),
        normalization_rules=SINOE_NORMALIZATION_RULES,
        dechet_mapping=source_sinoe_dechet_mapping_get(),
        product_mapping=get_mapping_config("sous_categories_sinoe"),
    ).to_airflow_params(),
) as dag:
    eo_task_chain(dag)
