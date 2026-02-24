"""DAG to anonymize QFDMO acteurs for RGPD"""

from airflow import DAG
from enrich.config.cohorts import COHORTS
from enrich.config.dbt import DBT
from enrich.config.models import EnrichActeursRGPDConfig
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
    dag_id="enrich_acteurs_rgpd",
    dag_display_name="🕵️ Enrichir - Acteurs RGPD",
    default_args=DEFAULT_ARGS_NO_RETRIES,
    description=("Un DAG pour anonymiser les acteurs vs. RGPD"),
    tags=[TAGS.ENRICH, TAGS.ANNAIRE_ENTREPRISE, TAGS.RGPD, TAGS.ACTEURS],
    schedule=None,
    start_date=START_DATES.DEFAULT,
    params=config_to_airflow_params(
        EnrichActeursRGPDConfig(
            dbt_models_refresh=True,
            filter_equals__acteur_statut="ACTIF",
        )
    ),
) as dag:
    # Instantiation
    config = enrich_config_create_task(dag)
    dbt_refresh = enrich_dbt_models_refresh_task(dag)
    suggest_rgpd = enrich_dbt_model_suggest_task(
        dag,
        task_id=TASKS.ENRICH_RGPD_SUGGESTIONS,
        cohort=COHORTS.RGPD,
        dbt_model_name=DBT.MARTS_ENRICH_RGPD_SUGGESTIONS,
    )
    config >> dbt_refresh >> suggest_rgpd  # type: ignore
