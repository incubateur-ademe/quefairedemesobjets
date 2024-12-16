from airflow import DAG
from sources.config.airflow_params import get_mapping_config
from sources.tasks.airflow_logic.operators import default_args, eo_task_chain

# FIXME: résoudre le problème de conflit entre formatteur VSCode
# et pré-commit qui ne sont pas d'accord sur la longueur des lignes
COL_POINT_APPORT_SERVICE = "point_dapport_de_service_reparation"
COL_POINT_COLLECTE = "point_de_collecte_ou_de_reprise_des_dechets"

with DAG(
    dag_id="eo-screlec",
    dag_display_name="Source - SCRELEC",
    default_args=default_args,
    description=(
        "DAG pour télécharger, standardiser, et charger dans notre base la source SINOE"
    ),
    tags=["source", "ademe", "screlec", "piles", "batteries", "accumulateurs"],
    params={
        "endpoint": (
            "https://data.ademe.fr/data-fair/api/v1/datasets/"
            "donnees-eo-screlec/lines?size=10000"
        ),
        "source_code": "SCRELEC",
        "column_mapping": {
            # ----------------------------------------
            # Champs à mapper
            # ----------------------------------------
            "adresse_format_ban": "adresse_format_ban",
            "ecoorganisme": "source_id",
            "enseigne_commerciale": "nom_commercial",
            "exclusivite_de_reprisereparation": "exclusivite_de_reprisereparation",
            "id_point_apport_ou_reparation": "identifiant_externe",
            "labels_etou_bonus": "labels_etou_bonus",
            "latitudewgs84": "latitude",
            "longitudewgs84": "longitude",
            "nom_de_lorganisme": "nom",
            COL_POINT_APPORT_SERVICE: COL_POINT_APPORT_SERVICE,
            COL_POINT_COLLECTE: COL_POINT_COLLECTE,
            "point_dapport_pour_reemploi": "point_dapport_pour_reemploi",
            "point_de_reparation": "point_de_reparation",
            "produitsdechets_acceptes": "produitsdechets_acceptes",
            "public_accueilli": "public_accueilli",
            "reprise": "reprise",
            "siret": "siret",
            "type_de_point_de_collecte": "acteur_type_id",
            "uniquement_sur_rdv": "uniquement_sur_rdv",
        },
        "column_to_drop": [
            "_geopoint",
            "_i",
            "_id",
            "_rand",
            "_score",
            "_updatedAt",
            "filiere",
            "accessible",
        ],
        "ignore_duplicates": False,
        "validate_address_with_ban": False,
        "product_mapping": get_mapping_config("sous_categories"),
    },
    schedule=None,
) as dag:
    eo_task_chain(dag)
