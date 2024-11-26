from airflow import DAG
from sources.config.airflow_params import (
    get_mapping_config,
    source_sinoe_dechet_mapping_get,
)
from sources.tasks.airflow_logic.operators import default_args, eo_task_chain

default_args["retries"] = 0
with DAG(
    dag_id="eo-sinoe",
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
        "source_code": "ADEME_SINOE_Decheteries",
        "column_mapping": {
            # Champs à conserver
            "C_SERVICE": "identifiant_externe",
            "N_SERVICE": "nom",
            "CP_SITE": "code_postal",
            "AD1_SITE": "adresse",
            "AD2_SITE": "adresse_complement",
            "L_VILLE_SITE": "ville",
            "TEL_SERVICE": "telephone",
            "LST_TYPE_DECHET": "produitsdechets_acceptes",
            "ORIGINE_DECHET_ACC": "public_accueilli",
            # GEO
            "_geopoint": "_geopoint",
            # 🔴 Champs nécessitant un traitement supplémentaire 🔴
            # représenté en EPSG:3857 WGS 84 / Pseudo-Mercator
            "GPS_X": None,
            "GPS_Y": None,
            "GPS_PRECISION": None,
            "GPS_QUALITY": None,
            #
            # 🔀 Mapping des sous-catégories
            # 🧹 Champs pour la déduplication
            "ANNEE": "ANNEE",
            # Champs que l'on n'a pas dans notre modèle acteur
            "D_OUV": None,
            "FAX_SERVICE": None,
            "D_MODIF": None,
            "LOV_MO_GEST": None,
            # Champs dérivés du code postale = à ignorer
            "C_DEPT": None,
            "C_REGION": None,
            "L_REGION": None,
            "N_DEPT": None,
            "C_COMM": None,  # code commune INSEE, pas utile
            # Champs concernant l'exploitant de la déchèterie
            # et non pas le site de la déchèterie = à ignorer
            "AD1_ACTEUR": None,
            "AD2_ACTEUR": None,
            "C_ACTEUR": None,
            "C_TYP_ACTEUR": None,
            "CP_ACTEUR": None,
            "FAX_ACTEUR": None,
            "L_TYP_ACTEUR": None,
            "L_VILLE_ACTEUR": None,
            "N_ACTEUR": None,
            "TEL_ACTEUR": None,
            # Champs système à ignorer
            "_i": None,
        },
        "dechet_mapping": source_sinoe_dechet_mapping_get(),
        "ignore_duplicates": False,
        "validate_address_with_ban": False,
        "product_mapping": get_mapping_config("sous_categories_sinoe"),
    },
    schedule=None,
) as dag:
    eo_task_chain(dag)
