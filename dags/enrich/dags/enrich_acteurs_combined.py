"""
DAG to anonymize QFDMO acteur which names
contains people from Annuaire Entreprise (AE)
"""

from airflow import DAG
from enrich.config import EnrichActeursPropertiesConfig
from enrich.tasks.airflow_logic.enrich_config_create_task import (
    enrich_config_create_task,
)
from enrich.tasks.airflow_logic.enrich_dbt_models_refresh_task import (
    enrich_dbt_models_refresh_task,
)
from shared.config import CATCHUPS, SCHEDULES, START_DATES, config_to_airflow_params

with DAG(
    dag_id="enrich_acteurs_combined",
    dag_display_name="🔢 Enrichir - Acteurs combinés (base + rev + displayed)",
    default_args={
        "owner": "airflow",
        "depends_on_past": False,
        "email_on_failure": False,
        "email_on_retry": False,
        "retries": 0,
    },
    description=("Un DAG des acteurs combinés (base + rev + displayed)"),
    tags=["acteurs", "base", "revision", "displayed", "combined"],
    schedule=SCHEDULES.DAILY,
    catchup=CATCHUPS.AWLAYS_FALSE,
    start_date=START_DATES.YESTERDAY,
    params=config_to_airflow_params(
        EnrichActeursPropertiesConfig(
            dbt_models_refresh=True,
            dbt_models_refresh_command=("dbt build --select marts_acteurs_combined"),
        )
    ),
) as dag:
    # Instantiation
    config = enrich_config_create_task(dag)
    dbt_refresh = enrich_dbt_models_refresh_task(dag)

    # Graph
    config >> dbt_refresh  # type: ignore
