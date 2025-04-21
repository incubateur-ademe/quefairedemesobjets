"""DAG to anonymize QFDMO acteurs for RGPD"""

from airflow import DAG
from enrich.config import (
    COHORTS,
    DBT,
    TASKS,
    EnrichActeursVillesConfig,
)
from enrich.tasks.airflow_logic.enrich_config_create_task import (
    enrich_config_create_task,
)
from enrich.tasks.airflow_logic.enrich_dbt_model_suggest_task import (
    enrich_dbt_model_suggest_task,
)
from enrich.tasks.airflow_logic.enrich_dbt_models_refresh_task import (
    enrich_dbt_models_refresh_task,
)
from shared.config import CATCHUPS, SCHEDULES, START_DATES, config_to_airflow_params

with DAG(
    dag_id="enrich_acteurs_villes",
    dag_display_name="🌆 Enrichir - Acteurs Villes",
    default_args={
        "owner": "airflow",
        "depends_on_past": False,
        "email_on_failure": False,
        "email_on_retry": False,
        "retries": 0,
    },
    description=("Un DAG pour anonymiser les acteurs vs. RGPD"),
    tags=["annuaire", "entreprises", "ae", "rgpd", "acteurs", "juridique"],
    schedule=SCHEDULES.NONE,
    catchup=CATCHUPS.AWLAYS_FALSE,
    start_date=START_DATES.YESTERDAY,
    params=config_to_airflow_params(
        EnrichActeursVillesConfig(
            dbt_models_refresh=True,
            dbt_models_refresh_command=(
                "dbt build --select tag:marts,tag:enrich,tag:villes"
            ),
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
