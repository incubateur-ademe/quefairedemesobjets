"""
DAG to suggest SIRET/SIREN enrichments for QFDMO acteurs:
- 1 cohorte to suggest a new SIRET for acteurs that have a known SIREN
- 1 cohorte to suggest a new SIREN for acteurs that have a known SIRET

Suggestions are grouped (1 SuggestionGroupe per proposed SIRET, resp. per SIRET
acteur) using
the non-legacy SuggestionGroupe/SuggestionUnitaire machinery, the same way
crawl_urls does with `use_legacy_suggestions=False`.
"""

from airflow import DAG
from airflow.sdk.bases.operator import chain
from enrich.config.cohorts import COHORTS
from enrich.config.dbt import DBT
from enrich.config.models import EnrichActeursSiretSirenConfig
from enrich.config.tasks import TASKS
from enrich.tasks.airflow_logic.enrich_dbt_models_task import (
    enrich_dbt_models_refresh_task,
    enrich_dbt_models_test_task,
)
from enrich.tasks.airflow_logic.enrich_siret_siren_suggest_task import (
    enrich_siret_siren_suggest_task,
)
from shared.config.airflow import DEFAULT_ARGS_NO_RETRIES
from shared.config.models import config_to_airflow_params
from shared.config.start_dates import START_DATES
from shared.config.tags import TAGS
from utils.docs import load_dag_doc_md

with DAG(
    dag_id="enrich_siret_siren",
    dag_display_name="🏢 Enrichir - Acteurs SIRET & SIREN",
    default_args=DEFAULT_ARGS_NO_RETRIES,
    description=(
        "Un DAG pour proposer un SIRET (depuis un SIREN connu) "
        "ou un SIREN (depuis un SIRET connu) pour les acteurs"
    ),
    doc_md=load_dag_doc_md("enrich-siret-siren.md"),
    tags=[
        TAGS.ENRICH,
        TAGS.SIREN,
        TAGS.SIRET,
        TAGS.ACTEURS,
        TAGS.SUGGESTIONS,
    ],
    schedule=None,
    start_date=START_DATES.DEFAULT,
    params=config_to_airflow_params(
        EnrichActeursSiretSirenConfig(
            dbt_models_refresh=True,
            dbt_models_refresh_command=(
                "dbt run --select +tag:siren_siret --exclude tag:normalisation"
            ),
            dbt_models_test_command=(
                "dbt test --select +tag:siren_siret --exclude tag:normalisation"
            ),
        ),
    ),
) as dag:
    dbt_refresh = enrich_dbt_models_refresh_task(dag)
    dbt_test = enrich_dbt_models_test_task(dag)

    # Cohorte 1: acteurs with a known SIREN -> suggest a new SIRET
    # 1 SuggestionGroupe per proposed SIRET
    suggest_siret_from_siren = enrich_siret_siren_suggest_task(
        dag,
        task_id=TASKS.ENRICH_SIRET_FROM_SIREN_SUGGESTIONS,
        cohort=COHORTS.SIRET_FROM_SIREN,
        dbt_model_name=DBT.MARTS_ENRICH_SIRET_FROM_SIREN,
        suggest_action="ENRICH_ACTEURS_SIRET",
        suggest_field="siret",
    )

    # Cohorte 2: acteurs with a known SIRET -> suggest a new SIREN
    # 1 SuggestionGroupe per SIRET
    suggest_siren_from_siret = enrich_siret_siren_suggest_task(
        dag,
        task_id=TASKS.ENRICH_SIREN_FROM_SIRET_SUGGESTIONS,
        cohort=COHORTS.SIREN_FROM_SIRET,
        dbt_model_name=DBT.MARTS_ENRICH_SIREN_FROM_SIRET,
        suggest_action="ENRICH_ACTEURS_SIREN",
        suggest_field="siren",
    )

    chain(
        dbt_refresh,
        dbt_test,
        [suggest_siret_from_siren, suggest_siren_from_siret],
    )
