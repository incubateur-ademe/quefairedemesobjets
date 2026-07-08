"""
DAG to clone AE's etablissement table in our DB.
"AE" abbreviates "Annuaire Entreprises" to prevent
running into DB table name length limits.
"""

from airflow import DAG
from airflow.sdk import Param
from airflow.sdk.definitions.param import ParamsDict
from clone.tasks.airflow_logic.chain_tasks import chain_tasks
from shared.config.airflow import DEFAULT_ARGS_NO_RETRIES
from shared.config.schedules import SCHEDULES
from shared.config.start_dates import START_DATES
from shared.config.tags import TAGS

with DAG(
    dag_id="clone_ae_etablissement",
    dag_display_name="Cloner - AE - Etablissement",
    default_args=DEFAULT_ARGS_NO_RETRIES,
    schedule=SCHEDULES.EVERY_FIRST_DAY_OF_MONTH_AT_01_00,
    start_date=START_DATES.DEFAULT,
    description=(
        "Clone la table 'etablissement' de l'Annuaire Entreprises (AE) dans notre DB"
    ),
    tags=[
        TAGS.ENRICH,
        TAGS.CLONE,
        TAGS.ANNAIRE_ENTREPRISE,
        TAGS.ETABLISSEMENT,
        TAGS.SIRET,
    ],
    params=ParamsDict(
        {
            "dry_run": Param(
                False,
                type="boolean",
                description_md="🚱 Si coché, aucune tâche d'écriture ne sera effectuée",
            ),
            "table_kind": Param(
                "ae_etablissement",
                type="string",
                description_md="📊 Le genre de table à créer",
            ),
            "data_endpoint": Param(
                "https://www.data.gouv.fr/api/1/datasets/r/0651fb76-bcf3-4f6a-a38d-bc04fa708576",
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
                "StockEtablissement_utf8.zip",
                type="string",
                description_md="📦 Nom du fichier téléchargé",
            ),
            "file_unpacked": Param(
                "StockEtablissement_utf8.csv",
                type="string",
                description_md="📦 Nom du fichier décompressé",
            ),
            "delimiter": Param(
                ",",
                type="string",
                description_md="🔤 Délimiteur utilisé dans le fichier",
            ),
        }
    ),
) as dag:
    chain_tasks(dag)
