from airflow import DAG
from sources.config.airflow_params import get_mapping_config
from sources.tasks.airflow_logic.operators import default_args, eo_task_chain

with DAG(
    dag_id="pharmacies",
    dag_display_name="Source - PHARMACIES",
    default_args=default_args,
    description=("Téléchargement des pharmacies (Ordre National Des Pharmaciens)"),
    params={
        "column_transformations": [
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
        ],
        "column_mapping": {
            "Numéro d'établissement": "identifiant_externe",
            "Téléphone": "telephone",
        },
        "endpoint": "https://www.ordre.pharmacien.fr/download/annuaire_csv.zip",
        "columns_to_add_by_default": {
            "statut": "ACTIF",
            "uniquement_sur_rdv": "non",
            "public_accueilli": "Particuliers",
            "produitsdechets_acceptes": "Médicaments & DASRI",
            "acteur_type_id": "pharmacie",
            "point_de_collecte_ou_de_reprise_des_dechets": True,
        },
        "source_code": "ordredespharmaciens",
        "product_mapping": get_mapping_config(),
    },
    schedule=None,
) as dag:
    eo_task_chain(dag)
