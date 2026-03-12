# https://etalab-datasets.geo.data.gouv.fr/contours-administratifs/latest/geojson/


from airflow import DAG
from airflow.sdk import Param
from clone.tasks.airflow_logic.chain_tasks import chain_tasks
from shared.config.airflow import DEFAULT_ARGS_NO_RETRIES
from shared.config.schedules import SCHEDULES
from shared.config.start_dates import START_DATES
from shared.config.tags import TAGS

with DAG(
    dag_id="clone_ca_epci",
    dag_display_name="Cloner - Contours Administratifs - EPCI",
    default_args=DEFAULT_ARGS_NO_RETRIES,
    schedule=SCHEDULES.EVERY_SUNDAY_AT_01_00,
    start_date=START_DATES.DEFAULT,
    description=(
        "Clone le jeu de données 'epci' de Contours Administratifs dans notre DB"
    ),
    tags=[
        TAGS.ENRICH,
        TAGS.CLONE,
        TAGS.CONTOURS_ADMINISTRATIFS,
        TAGS.EPCI,
    ],
    params={
        "dry_run": Param(
            False,
            type="boolean",
            description_md="🚱 Si coché, aucune tâche d'écriture ne sera effectuée",
        ),
        "table_kind": Param(
            "ca_epci",
            type="string",
            description_md="📊 Le genre de table à créer",
        ),
        "data_endpoint": Param(
            (
                "https://etalab-datasets.geo.data.gouv.fr/contours-administratifs/"
                "latest/geojson/epci-50m.geojson.gz"
            ),
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
            "epci-50m.geojson.gz",
            type="string",
            description_md="📦 Nom du fichier téléchargé",
        ),
        "file_unpacked": Param(
            "epci-50m.geojson",
            type="string",
            description_md="📦 Nom du fichier décompressé",
        ),
    },
) as dag:
    chain_tasks(dag)
