"""
DAG to clone AE's unite_legale table in our DB.
"AE" abbreviates "Annuaire Entreprises" to prevent
running into DB table name length limits.
"""

from datetime import datetime

from airflow import DAG
from airflow.models.param import Param
from clone.tasks.airflow_logic.chain_tasks import chain_tasks

with DAG(
    dag_id="clone_ae_unite_legale",
    dag_display_name="Cloner - AE - Unite Legale",
    default_args={
        "owner": "airflow",
        "depends_on_past": False,
        "start_date": datetime(2025, 3, 5),
        "catchup": False,
        "email_on_failure": False,
        "email_on_retry": False,
        "retries": 0,
    },
    description=("Un DAG pour répliquer l'Annuaire Entreprise (AE) dans notre DB"),
    tags=["clone", "annuaire", "entreprise", "unite_legale", "siren", "ae"],
    params={
        "dry_run": Param(
            False,
            type="boolean",
            description_md="🚱 Si coché, aucune tâche d'écriture ne sera effectuée",
        ),
        "table_kind": Param(
            "ae_unite_legale",
            type="string",
            description_md="📊 Le genre de table à créer",
        ),
        "data_url": Param(
            "https://files.data.gouv.fr/insee-sirene/StockUniteLegale_utf8.zip",
            type="string",
            description_md="📥 URL pour télécharger les données",
        ),
        "file_downloaded": Param(
            "StockUniteLegale_utf8.zip",
            type="string",
            description_md="📦 Nom du fichier téléchargé",
        ),
        "file_unpacked": Param(
            "StockUniteLegale_utf8.csv",
            type="string",
            description_md="📦 Nom du fichier décompressé",
        ),
    },
    schedule=None,
    catchup=False,
) as dag:
    chain_tasks(dag)
