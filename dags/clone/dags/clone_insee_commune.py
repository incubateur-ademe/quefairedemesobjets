"""
DAG to clone INSEE's commune table in our DB.

cf. https://www.data.gouv.fr/datasets/code-officiel-geographique-cog/
-> Liste des communes, arrondissements municipaux, communes déléguées et communes
   associées au 1er janvier 2025, avec le code des niveaux supérieurs (canton ou
   pseudo-canton, département, région)
cf. https://explore.data.gouv.fr/fr/datasets/58c984b088ee386cdb1261f3/#/resources/91a95bee-c7c8-45f9-a8aa-f14cc4697545
"""

from airflow import DAG
from airflow.models.param import Param
from clone.tasks.airflow_logic.chain_tasks import chain_tasks
from shared.config.airflow import DEFAULT_ARGS_NO_RETRIES
from shared.config.schedules import SCHEDULES
from shared.config.start_dates import START_DATES
from shared.config.tags import TAGS

with DAG(
    dag_id="clone_insee_commune",
    dag_display_name="Cloner - INSEE - Commune",
    default_args=DEFAULT_ARGS_NO_RETRIES,
    schedule=SCHEDULES.EVERY_SUNDAY_AT_00_00,
    start_date=START_DATES.DEFAULT,
    description=("Clone le jeu de données 'commune' de INSEE dans notre DB"),
    tags=[
        TAGS.ENRICH,
        TAGS.CLONE,
        TAGS.INSEE,
        TAGS.COMMUNE,
    ],
    params={
        "dry_run": Param(
            False,
            type="boolean",
            description_md="🚱 Si coché, aucune tâche d'écriture ne sera effectuée",
        ),
        "table_kind": Param(
            "insee_commune",
            type="string",
            description_md="📊 Le genre de table à créer",
        ),
        "data_endpoint": Param(
            "https://www.insee.fr/fr/statistiques/fichier/8377162/v_commune_2025.csv",
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
