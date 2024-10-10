from airflow import DAG
from utils.eo_operators import default_args, pharma_task_chain

with DAG(
    dag_id="pharmacies",
    dag_display_name="Téléchargement des pharmacies (Ordre National Des Pharmaciens)",
    default_args=default_args,
    description=("Téléchargement des pharmacies (Ordre National Des Pharmaciens)"),
    params={
        "endpoint": ("https://www.ordre.pharmacien.fr/download/annuaire_csv.zip"),
        "fixed_columns": {
            "uniquement_sur_rdv": "non",
            "public_accueilli": "Particuliers",
            "produitsdechets_acceptes": "Médicaments & DASRI",
            "ecoorganisme": "Ordre National Des Pharmaciens",
            "Type établissement": "pharmacie",
            "point_de_collecte_ou_de_reprise_des_dechets": True,
        },
        "geolocation": True,
        "column_mapping": {
            "Numéro d'établissement": "identifiant_externe",
            "Type établissement": "acteur_type_id",
            "Dénomination commerciale": "nom",
            "Raison sociale": "nom_officiel",
            "Adresse": "adresse",
            "Code postal": "code_postal",
            "Commune": "ville",
            "Téléphone": "telephone",
            "ecoorganisme": "source_id",
            "produitsdechets_acceptes": "produitsdechets_acceptes",
            "public_accueilli": "public_accueilli",
            "uniquement_sur_rdv": "uniquement_sur_rdv",
        },
    },
    schedule=None,
) as dag:
    pharma_task_chain(dag)
