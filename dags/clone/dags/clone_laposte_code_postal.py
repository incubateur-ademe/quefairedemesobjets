"""
DAG to clone LAPOSTE's codes_postaux table in our DB.

cf. https://www.data.gouv.fr/datasets/base-officielle-des-codes-postaux/
"""

from airflow import DAG
from airflow.models.param import Param
from clone.tasks.airflow_logic.chain_tasks import chain_tasks
from shared.config.airflow import DEFAULT_ARGS_NO_RETRIES
from shared.config.schedules import SCHEDULES
from shared.config.start_dates import START_DATES
from shared.config.tags import TAGS

with DAG(
    dag_id="clone_laposte_codes_postaux",
    dag_display_name="Cloner - LAPOSTE - Codes Postaux vs codes INSEE",
    default_args=DEFAULT_ARGS_NO_RETRIES,
    schedule=SCHEDULES.EVERY_SUNDAY_AT_02_00,
    start_date=START_DATES.DEFAULT,
    description=("Clone le jeu de données 'code postal' de LAPOSTE dans notre DB"),
    tags=[
        TAGS.ENRICH,
        TAGS.CLONE,
        TAGS.LAPOSTE,
        TAGS.CP,
    ],
    params={
        "dry_run": Param(
            False,
            type="boolean",
            description_md="🚱 Si coché, aucune tâche d'écriture ne sera effectuée",
        ),
        "table_kind": Param(
            "laposte_code_postal",
            type="string",
            description_md="📊 Le genre de table à créer",
        ),
        "clone_method": Param(
            "download_to_disk_first",
            type="string",
            description_md=r"""📥 **Méthode de création** de la table:
            - `download_to_disk_first`: télécharge/unpack sur disque avant import DB
            pas de stream possible pour ce jeu de données
            """,
            enum=["download_to_disk_first"],
        ),
        "file_downloaded": Param(
            "laposte_code_postal.csv",
            type="string",
            description_md="📦 Nom du fichier téléchargé",
        ),
        "data_endpoint": Param(
            "https://datanova.laposte.fr/data-fair/api/v1/datasets/laposte-hexasmal/raw",
            type="string",
            description_md="📥 URL pour télécharger les données",
        ),
        "delimiter": Param(
            ";",
            type="string",
            description_md="🔤 Délimiteur utilisé dans le fichier",
        ),
        "convert_downloaded_file_to_utf8": Param(
            True,
            type="boolean",
            description_md="🔤 Convertir le fichier téléchargé de ISO-8859-1 en UTF-8",
        ),
    },
) as dag:
    chain_tasks(dag)
