"""DAG to suggestion city corrections based on BAN data"""

from airflow import DAG
from enrich.config.cohorts import COHORTS
from enrich.config.dbt import DBT
from enrich.config.models import EnrichActeursVillesConfig
from enrich.config.tasks import TASKS
from enrich.tasks.airflow_logic.enrich_config_create_task import (
    enrich_config_create_task,
)
from enrich.tasks.airflow_logic.enrich_dbt_model_suggest_task import (
    enrich_dbt_model_suggest_task,
)
from enrich.tasks.airflow_logic.enrich_dbt_models_refresh_task import (
    enrich_dbt_models_refresh_task,
)
from shared.config.airflow import DEFAULT_ARGS_NO_RETRIES
from shared.config.models import config_to_airflow_params
from shared.config.start_dates import START_DATES
from shared.config.tags import TAGS

with DAG(
    dag_id="enrich_acteurs_villes",
    dag_display_name="🌆 Enrichir - Acteurs Villes",
    default_args=DEFAULT_ARGS_NO_RETRIES,
    description=("Un DAG pour suggérer des corrections de villes"),
    tags=[TAGS.ENRICH, TAGS.ANNAIRE_ENTREPRISE, TAGS.ACTEURS, TAGS.CP, TAGS.VILLES],
    schedule=None,
    start_date=START_DATES.DEFAULT,
    params=config_to_airflow_params(
        EnrichActeursVillesConfig(
            dbt_models_refresh=True,
            dbt_models_refresh_command=(
                "dbt build --select tag:marts,tag:enrich,tag:villes"
            ),
            filter_equals__acteur_statut="ACTIF",
        )
    ),
) as dag:
    # Instantiation
    config = enrich_config_create_task(dag)
    dbt_refresh = enrich_dbt_models_refresh_task(dag)
    suggest_typo = enrich_dbt_model_suggest_task(
        dag,
        task_id=TASKS.ENRICH_VILLES_TYPO,
        cohort=COHORTS.VILLES_TYPO,
        dbt_model_name=DBT.MARTS_ENRICH_VILLES_TYPO,
    )
    suggest_new = enrich_dbt_model_suggest_task(
        dag,
        task_id=TASKS.ENRICH_VILLES_NEW,
        cohort=COHORTS.VILLES_NEW,
        dbt_model_name=DBT.MARTS_ENRICH_VILLES_NEW,
    )
    config >> dbt_refresh  # type: ignore
    dbt_refresh >> suggest_typo  # type: ignore
    dbt_refresh >> suggest_new  # type: ignore
