"""
DAG to clone BAN's adresses table in our DB.
"BAN" abbreviates "Base Adresse Nationale" to prevent
running into DB table name length limits.
"""

from airflow import DAG
from airflow.sdk import Param
from clone.config.models import FIX_CORRUPTED_UTF8_SED_SUBSTITUTION_DESCRIPTION
from clone.tasks.airflow_logic.chain_tasks import chain_tasks
from clone.tasks.airflow_logic.clone_dbt_task import clone_dbt_params
from shared.config.airflow import DEFAULT_ARGS_NO_RETRIES
from shared.config.schedules import SCHEDULES
from shared.config.start_dates import START_DATES
from shared.config.tags import TAGS

with DAG(
    dag_id="clone_ban_adresses",
    dag_display_name="Cloner - BAN - Adresses",
    default_args=DEFAULT_ARGS_NO_RETRIES,
    schedule=SCHEDULES.EVERY_FIRST_DAY_OF_MONTH_AT_04_00,
    start_date=START_DATES.DEFAULT,
    description=(
        "Clone la table 'adresses' de la Base Adresse Nationale (BAN) dans notre DB"
    ),
    tags=[TAGS.ENRICH, TAGS.CLONE, TAGS.BAN, TAGS.ADRESSES],
    params={
        "dry_run": Param(
            False,
            type="boolean",
            description_md="🚱 Si coché, aucune tâche d'écriture ne sera effectuée",
        ),
        "table_kind": Param(
            "ban_adresses",
            type="string",
            description_md="📊 Le genre de table à créer",
        ),
        "data_endpoint": Param(
            "https://adresse.data.gouv.fr/data/ban/adresses/latest/csv/adresses-france.csv.gz",
            type="string",
            description_md="📥 URL pour télécharger les données",
        ),
        "clone_method": Param(
            "download_to_disk_first",
            type="string",
            description_md=r"""📥 **Méthode de création** de la table:
            - `download_to_disk_first`: télécharge/unpack sur disque avant import DB
            - `stream_directly`: télécharge/unpack/charge en DB à la volée
            """,
            enum=["download_to_disk_first", "stream_directly"],
        ),
        "file_downloaded": Param(
            "adresses-france.csv.gz",
            type="string",
            description_md="📦 Nom du fichier téléchargé",
        ),
        "file_unpacked": Param(
            "adresses-france.csv",
            type="string",
            description_md="📦 Nom du fichier décompressé",
        ),
        "delimiter": Param(
            ";",
            type="string",
            description_md="🔤 Délimiteur utilisé dans le fichier",
        ),
        "fix_corrupted_utf8_sed_substitutions": Param(
            [],
            type="array",
            description_md=FIX_CORRUPTED_UTF8_SED_SUBSTITUTION_DESCRIPTION,
        ),
        **clone_dbt_params(dbt_select="tag:ban,tag:normalisation"),
    },
) as dag:
    chain_tasks(dag)
