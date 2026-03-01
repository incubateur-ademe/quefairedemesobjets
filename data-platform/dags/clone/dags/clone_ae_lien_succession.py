"""
DAG to clone AE's liens de succession table in our DB.
"AE" abbreviates "Annuaire Entreprises" to prevent
running into DB table name length limits.

cf. https://www.data.gouv.fr/datasets/base-sirene-des-entreprises-et-de-leurs-etablissements-siren-siret/
"""

from airflow import DAG
from airflow.models.param import Param
from clone.tasks.airflow_logic.chain_tasks import chain_tasks
from shared.config.airflow import DEFAULT_ARGS_NO_RETRIES
from shared.config.start_dates import START_DATES
from shared.config.tags import TAGS

with DAG(
    dag_id="clone_ae_lien_succession",
    dag_display_name="Cloner - AE - Lien de Succession",
    default_args=DEFAULT_ARGS_NO_RETRIES,
    schedule=None,
    start_date=START_DATES.DEFAULT,
    description=(
        "Clone la table 'lien de succession' de l'Annuaire Entreprises (AE)"
        " dans notre DB"
    ),
    tags=[
        TAGS.ENRICH,
        TAGS.CLONE,
        TAGS.ANNAIRE_ENTREPRISE,
        TAGS.ETABLISSEMENT,
        TAGS.SIRET,
    ],
    params={
        "dry_run": Param(
            False,
            type="boolean",
            description_md="🚱 Si coché, aucune tâche d'écriture ne sera effectuée",
        ),
        "table_kind": Param(
            "ae_lien_succession",
            type="string",
            description_md="📊 Le genre de table à créer",
        ),
        "data_endpoint": Param(
            "https://www.data.gouv.fr/api/1/datasets/r/9c4d5d9c-4bbb-4b9c-837a-6155cb589e26",
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
            "StockEtablissementLiensSuccession_utf8.zip",
            type="string",
            description_md="📦 Nom du fichier téléchargé",
        ),
        "file_unpacked": Param(
            "StockEtablissementLiensSuccession_utf8.csv",
            type="string",
            description_md="📦 Nom du fichier décompressé",
        ),
        "delimiter": Param(
            ",",
            type="string",
            description_md="🔤 Délimiteur utilisé dans le fichier",
        ),
    },
) as dag:
    chain_tasks(dag)
