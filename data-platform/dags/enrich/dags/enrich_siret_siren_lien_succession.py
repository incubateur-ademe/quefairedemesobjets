"""
DAG to suggest SIRET/SIREN replacements from AE lien succession for QFDMO acteurs.

Suggestions are grouped by the full replacement mapping:
(source SIREN, source SIRET) -> (target SIREN, target SIRET).
"""

from airflow import DAG
from airflow.sdk.bases.operator import chain
from enrich.config.cohorts import COHORTS
from enrich.config.dbt import DBT
from enrich.config.models import EnrichActeursLienSuccessionConfig
from enrich.config.tasks import TASKS
from enrich.tasks.airflow_logic.enrich_dbt_models_task import (
    enrich_dbt_models_refresh_task,
    enrich_dbt_models_test_task,
)
from enrich.tasks.airflow_logic.enrich_lien_succession_suggest_task import (
    enrich_lien_succession_suggest_task,
)
from shared.config.airflow import DEFAULT_ARGS_NO_RETRIES
from shared.config.models import config_to_airflow_params
from shared.config.start_dates import START_DATES
from shared.config.tags import TAGS
from utils.docs import load_dag_doc_md

with DAG(
    dag_id="enrich_siret_siren_lien_succession",
    dag_display_name="🏢 Enrichir - Acteurs SIRET & SIREN (lien succession)",
    default_args=DEFAULT_ARGS_NO_RETRIES,
    description=(
        "Un DAG pour proposer un couple SIREN/SIRET successeur "
        "depuis les liens de succession AE"
    ),
    doc_md=load_dag_doc_md("enrich-siret-siren-lien-succession.md"),
    tags=[
        TAGS.ENRICH,
        TAGS.SIREN,
        TAGS.SIRET,
        TAGS.ACTEURS,
        TAGS.SUGGESTIONS,
        TAGS.ANNAIRE_ENTREPRISE,
    ],
    schedule=None,
    start_date=START_DATES.DEFAULT,
    params=config_to_airflow_params(
        EnrichActeursLienSuccessionConfig(
            dbt_models_refresh=True,
            dbt_models_refresh_command="dbt run --select +tag:lien_succession",
            dbt_models_test_command="dbt test --select +tag:lien_succession",
        ),
    ),
) as dag:
    dbt_refresh = enrich_dbt_models_refresh_task(dag)
    dbt_test = enrich_dbt_models_test_task(dag)

    suggest_lien_succession = enrich_lien_succession_suggest_task(
        dag,
        task_id=TASKS.ENRICH_LIEN_SUCCESSION_SUGGESTIONS,
        cohort=COHORTS.LIEN_SUCCESSION,
        dbt_model_name=DBT.EXPOSURE_STATS_ACTEUR_SIRET_SUCCESSEUR,
        suggest_action="ENRICH_ACTEURS_LIEN_SUCCESSION",
    )

    chain(dbt_refresh, dbt_test, suggest_lien_succession)
