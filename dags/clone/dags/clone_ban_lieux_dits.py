"""
DAG to clone BAN's lieux_dits table in our DB.
"BAN" abbreviates "Base Adresse Nationale" to prevent
running into DB table name length limits.
"""

from airflow import DAG
from airflow.models.param import Param
from clone.tasks.airflow_logic.chain_tasks import chain_tasks
from shared.config import SCHEDULES, START_DATES, CATCHUPS

with DAG(
    dag_id="clone_ban_lieux_dits",
    dag_display_name="Cloner - BAN - Lieux-dits",
    default_args={
        "owner": "airflow",
        "depends_on_past": False,
        "email_on_failure": False,
        "email_on_retry": False,
        "retries": 0,
    },
    schedule=SCHEDULES.NONE,
    catchup=CATCHUPS.AWLAYS_FALSE,
    start_date=START_DATES.YESTERDAY,
    description=(
        "Clone la table 'lieux_dits' de la Base Adresse Nationale (BAN) dans notre DB"
    ),
    tags=["clone", "ban", "adresses", "lieux_dits"],
    params={
        "dry_run": Param(
            False,
            type="boolean",
            description_md="🚱 Si coché, aucune tâche d'écriture ne sera effectuée",
        ),
        "table_kind": Param(
            "ban_lieux_dits",
            type="string",
            description_md="📊 Le genre de table à créer",
        ),
        "data_url": Param(
            "https://adresse.data.gouv.fr/data/ban/adresses/latest/csv/lieux-dits-beta-france.csv.gz",
            type="string",
            description_md="📥 URL pour télécharger les données",
        ),
        "file_downloaded": Param(
            "lieux-dits-beta-france.csv.gz",
            type="string",
            description_md="📦 Nom du fichier téléchargé",
        ),
        "file_unpacked": Param(
            "lieux-dits-beta-france.csv",
            type="string",
            description_md="📦 Nom du fichier décompressé",
        ),
        "delimiter": Param(
            ";",
            type="string",
            description_md="🔤 Délimiteur utilisé dans le fichier",
        ),
    },
) as dag:
    chain_tasks(dag)
