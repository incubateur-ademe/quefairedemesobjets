"""
DAG to clone Koumoul's epci table in our DB.

cf. https://opendata.koumoul.com/datasets/communes-de-france/full
"""

from airflow import DAG
from airflow.models.param import Param
from clone.tasks.airflow_logic.chain_tasks import chain_tasks
from shared.config.airflow import DEFAULT_ARGS_NO_RETRIES
from shared.config.schedules import SCHEDULES
from shared.config.start_dates import START_DATES
from shared.config.tags import TAGS

with DAG(
    dag_id="clone_koumoul_epci",
    dag_display_name="Cloner - Koumoul - EPCI",
    default_args=DEFAULT_ARGS_NO_RETRIES,
    schedule=SCHEDULES.EVERY_SUNDAY_AT_01_00,
    start_date=START_DATES.DEFAULT,
    description=("Clone le jeu de données 'epci' de Koumoul dans notre DB"),
    tags=[
        TAGS.ENRICH,
        TAGS.CLONE,
        TAGS.KOUMOUL,
        TAGS.EPCI,
    ],
    params={
        "dry_run": Param(
            False,
            type="boolean",
            description_md="🚱 Si coché, aucune tâche d'écriture ne sera effectuée",
        ),
        "table_kind": Param(
            "koumoul_epci",
            type="string",
            description_md="📊 Le genre de table à créer",
        ),
        "data_endpoint": Param(
            (
                "https://opendata.koumoul.com/data-fair/api/v1/datasets/"
                "communes-de-france/data-files/Code Officiel Géographie.csv"
            ),
            type="string",
            description_md="📥 URL pour télécharger les données",
        ),
        "delimiter": Param(
            ",",
            type="string",
            description_md="🔤 Délimiteur utilisé dans le fichier",
        ),
    },
) as dag:
    chain_tasks(dag)
