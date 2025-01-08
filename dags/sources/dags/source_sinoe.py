from airflow import DAG
from sources.config.airflow_params import (
    get_mapping_config,
    source_sinoe_dechet_mapping_get,
)
from sources.tasks.airflow_logic.operators import default_args, eo_task_chain

default_args["retries"] = 0
with DAG(
    dag_id="sinoe",
    dag_display_name="Source - SINOE",
    default_args=default_args,
    description=(
        "DAG pour télécharger, standardiser, et charger dans notre base la source SINOE"
    ),
    tags=["source", "ademe", "sinoe", "déchèteries"],
    params={
        "endpoint": (
            "https://data.ademe.fr/data-fair/api/v1/datasets/"
            "sinoe-(r)-annuaire-des-decheteries-dma/lines?size=10000&q_mode=simple&ANNEE_eq=2024"
        ),
        "normalization_rules": [
            # 1. Renommage des colonnes
            {
                "origin": "C_SERVICE",
                "destination": "identifiant_externe",
            },
            {
                "origin": "N_SERVICE",
                "destination": "nom",
            },
            {
                "origin": "AD1_SITE",
                "destination": "adresse",
            },
            {
                "origin": "AD2_SITE",
                "destination": "adresse_complement",
            },
            {
                "origin": "L_VILLE_SITE",
                "destination": "ville",
            },
            # 2. Transformation des colonnes
            {
                "origin": "CP_SITE",
                "transformation": "clean_code_postal",
                "destination": "code_postal",
            },
            {
                "origin": "LST_TYPE_DECHET",
                "transformation": "clean_souscategorie_codes_sinoe",
                "destination": "souscategorie_codes",
            },
            {
                "origin": "ORIGINE_DECHET_ACC",
                "transformation": "clean_public_accueilli",
                "destination": "public_accueilli",
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
                "column": "acteurservice_codes",
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
            # 4. Transformation du dataframe
            {
                "origin": ["_geopoint"],
                "transformation": "get_latlng_from_geopoint",
                "destination": ["latitude", "longitude"],
            },
            {
                "origin": ["TEL_SERVICE", "code_postal"],
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
            # 5. Supression des colonnes
            {"remove": "_geopoint"},
            {"remove": "_i"},
            {"remove": "_id"},
            {"remove": "_rand"},
            {"remove": "_score"},
            {"remove": "AD1_ACTEUR"},
            {"remove": "AD2_ACTEUR"},
            {"remove": "C_ACTEUR"},
            {"remove": "C_COMM"},
            {"remove": "C_DEPT"},
            {"remove": "C_REGION"},
            {"remove": "C_TYP_ACTEUR"},
            {"remove": "CP_ACTEUR"},
            {"remove": "D_MODIF"},
            {"remove": "D_OUV"},
            {"remove": "FAX_ACTEUR"},
            {"remove": "FAX_SERVICE"},
            {"remove": "GPS_LAT"},
            {"remove": "GPS_LONG"},
            {"remove": "GPS_PRECISION"},
            {"remove": "GPS_QUALITY"},
            {"remove": "GPS_X"},
            {"remove": "GPS_Y"},
            {"remove": "L_REGION"},
            {"remove": "L_TYP_ACTEUR"},
            {"remove": "L_VILLE_ACTEUR"},
            {"remove": "LOV_MO_GEST"},
            {"remove": "N_ACTEUR"},
            {"remove": "N_DEPT"},
            {"remove": "TEL_ACTEUR"},
            {"remove": "TEL_SERVICE"},
            # 6. Colonnes à garder (rien à faire, utilisé pour le controle)
            {"keep": "_geopoint"},  # FIXME : trnsformation explicite à faire ?
            {"keep": "ANNEE"},
        ],
        "dechet_mapping": source_sinoe_dechet_mapping_get(),
        "ignore_duplicates": False,
        "validate_address_with_ban": False,
        "product_mapping": get_mapping_config("sous_categories_sinoe"),
    },
    schedule=None,
) as dag:
    eo_task_chain(dag)
