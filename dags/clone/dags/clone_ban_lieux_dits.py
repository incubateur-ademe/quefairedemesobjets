"""
DAG to clone BAN's lieux_dits table in our DB.
"BAN" abbreviates "Base Adresse Nationale" to prevent
running into DB table name length limits.
"""

from airflow import DAG
from airflow.models.param import Param
from clone.tasks.airflow_logic.chain_tasks import chain_tasks
from shared.config import CATCHUPS, SCHEDULES, START_DATES

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
        "data_endpoint": Param(
            "https://adresse.data.gouv.fr/data/ban/adresses/latest/csv/lieux-dits-beta-france.csv.gz",
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
        "dbt_build_skip": Param(
            False,
            type="boolean",
            description_md="🚫 Si coché, le build DBT ne sera pas exécuté",
        ),
        "dbt_build_command": Param(
            "dbt build --select tag:ban,tag:lieux_dits",
            type="string",
            description_md="🔨 Commande DBT à exécuter",
        ),
    },
) as dag:
    chain_tasks(dag)
