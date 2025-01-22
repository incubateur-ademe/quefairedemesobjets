from airflow import DAG
from sources.config import shared_constants as constants
from sources.config.airflow_params import get_mapping_config
from sources.tasks.airflow_logic.operators import default_args, eo_task_chain

with DAG(
    dag_id="pharmacies",
    dag_display_name="Source - PHARMACIES",
    default_args=default_args,
    description=("Téléchargement des pharmacies (Ordre National Des Pharmaciens)"),
    params={
        "normalization_rules": [
            # 1. Renommage des colonnes
            # 2. Transformation des colonnes
            {
                "origin": "Raison sociale",
                "transformation": "strip_string",
                "destination": "nom",
            },
            {
                "origin": "Dénomination commerciale",
                "transformation": "strip_string",
                "destination": "nom_commercial",
            },
            {
                "origin": "Adresse",
                "transformation": "strip_string",
                "destination": "adresse",
            },
            {
                "origin": "Code postal",
                "transformation": "strip_string",
                "destination": "code_postal",
            },
            {
                "origin": "Commune",
                "transformation": "strip_string",
                "destination": "ville",
            },
            {
                "column": "source_code",
                "value": "ordredespharmaciens",
            },
            # 3. Ajout des colonnes avec une valeur par défaut
            {
                "column": "statut",
                "value": constants.ACTEUR_ACTIF,
            },
            {
                "column": "uniquement_sur_rdv",
                "value": "non",
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
                "column": "label_codes",
                "value": [],
            },
            {
                "column": "souscategorie_codes",
                "value": ["medicaments"],
            },
            {
                "column": "public_accueilli",
                "value": constants.PUBLIC_PAR,
            },
            {
                "column": "acteur_type_code",
                "value": "commerce",
            },
            # 4. Transformation du dataframe
            {
                "origin": ["Téléphone", "code_postal"],
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
            {"remove": "Téléphone"},
            {"remove": "Région"},
            {"remove": "Fax"},
            {"remove": "Département"},
            {"remove": "Type établissement"},
            # 6. Colonnes à garder (rien à faire, utilisé pour le controle)
        ],
        "endpoint": "https://www.ordre.pharmacien.fr/download/annuaire_csv.zip",
        "validate_address_with_ban": False,
        "product_mapping": get_mapping_config(),
    },
    schedule=None,
) as dag:
    eo_task_chain(dag)
