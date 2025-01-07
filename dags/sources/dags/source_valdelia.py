from airflow import DAG
from sources.config import shared_constants as constants
from sources.config.airflow_params import get_mapping_config
from sources.tasks.airflow_logic.operators import default_args, eo_task_chain

with DAG(
    dag_id="eo-valdelia",
    dag_display_name="Source - VALDELIA",
    default_args=default_args,
    description=(
        "A pipeline to fetch, process, and load to validate data into postgresql"
        " for Valdelia dataset"
    ),
    params={
        "normalization_rules": [
            # 1. Renommage des colonnes
            {
                "origin": "ecoorganisme",
                "destination": "source_code",
            },
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
            # {
            #     "origin": "site_web",
            #     "transformation": "clean_url",
            #     "destination": "url",
            # },
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
                "transformation": "clean_souscategorie_codes",
                "destination": "souscategorie_codes",
            },
            # 3. Ajout des colonnes avec une valeur par défaut
            {
                "column": "statut",
                "value": constants.ACTEUR_ACTIF,
            },
            # {
            #     "column": "label_codes",
            #     "value": [],
            # },
            # 4. Transformation du dataframe
            {
                "origin": ["labels_etou_bonus", "acteur_type_code"],
                "transformation": "clean_label_codes",
                "destination": ["label_codes"],
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
                "origin": ["siret", "siren"],
                "transformation": "clean_siret_and_siren",
                "destination": ["siret", "siren"],
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
                    "point_dapport_de_service_reparation",
                    "point_de_reparation",
                    "point_dapport_pour_reemploi",
                    "point_de_collecte_ou_de_reprise_des_dechets",
                ],
                "transformation": "clean_acteurservice_codes",
                "destination": ["acteurservice_codes"],
            },
            {
                "origin": [
                    "point_dapport_de_service_reparation",
                    "point_de_reparation",
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
            {"remove": "labels_etou_bonus"},
            {"remove": "point_dapport_de_service_reparation"},
            {"remove": "point_dapport_pour_reemploi"},
            {"remove": "point_de_reparation"},
            # 6. Colonnes à garder (rien à faire, utilisé pour le controle)
        ],
        "column_mapping": {
            "id_point_apport_ou_reparation": "identifiant_externe",
            "type_de_point_de_collecte": "acteur_type_id",
            "exclusivite_de_reprisereparation": "exclusivite_de_reprisereparation",
            "uniquement_sur_rdv": "uniquement_sur_rdv",
            "public_accueilli": "public_accueilli",
            "reprise": "reprise",
            "siret": "siret",
            "telephone": "telephone",
            "produitsdechets_acceptes": "produitsdechets_acceptes",
            "labels_etou_bonus": "labels_etou_bonus",
            "point_de_reparation": "point_de_reparation",
            "ecoorganisme": "source_id",
            "adresse_format_ban": "adresse_format_ban",
            "nom_de_lorganisme": "nom",
            "perimetre_dintervention": "perimetre_dintervention",
            "longitudewgs84": "longitude",
            "latitudewgs84": "latitude",
        },
        "columns_to_add_by_default": {
            "statut": constants.ACTEUR_ACTIF,
        },
        "endpoint": (
            "https://data.pointsapport.ademe.fr/data-fair/api/v1/datasets/"
            "donnees-eo-valdelia/lines?size=10000"
        ),
        "ignore_duplicates": False,
        "validate_address_with_ban": False,
        "product_mapping": get_mapping_config(),
    },
    schedule=None,
) as dag:
    eo_task_chain(dag)
