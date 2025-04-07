"""
DAG to clone AE's unite_legale table in our DB.
"AE" abbreviates "Annuaire Entreprises" to prevent
running into DB table name length limits.
"""

from airflow import DAG
from airflow.models.param import Param
from clone.tasks.airflow_logic.chain_tasks import chain_tasks
from shared.config import CATCHUPS, SCHEDULES, START_DATES

with DAG(
    dag_id="clone_ae_unite_legale",
    dag_display_name="Cloner - AE - Unite Legale",
    default_args={
        "owner": "airflow",
        "depends_on_past": False,
        "email_on_failure": False,
        "email_on_retry": False,
        "retries": 0,
    },
    schedule=SCHEDULES.NONE,
    catchup=CATCHUPS.AWLAYS_FALSE,
    start_date=START_DATES.FOR_SCHEDULE_NONE,
    description=(
        "Clone la table 'unite_legale' de l'Annuaire Entreprises (AE) dans notre DB"
    ),
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
        "data_endpoint": Param(
            "https://files.data.gouv.fr/insee-sirene/StockUniteLegale_utf8.zip",
            type="string",
            description_md="📥 URL pour télécharger les données",
        ),
        "clone_method": Param(
            "stream_directly",
            type="string",
            description_md=r"""📥 **Méthode de création** de la table:
            - `download_to_disk_first`: télécharge/unpack sur disque avant import DB
            - `stream_directly`: télécharge/unpack/charge en DB à la volée
            """,
            enum=["download_to_disk_first", "stream_directly"],
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
        "delimiter": Param(
            ",",
            type="string",
            description_md="🔤 Délimiteur utilisé dans le fichier",
        ),
        "dbt_build_skip": Param(
            False,
            type="boolean",
            description_md="🚫 Si coché, la build DBT ne sera pas exécuté",
        ),
        "dbt_build_command": Param(
            "dbt build --select tag:ae,tag:unite_legale",
            type="string",
            description_md="🔨 Commande DBT à exécuter",
        ),
    },
) as dag:
    chain_tasks(dag)
