"""
DAG to anonymize QFDMO acteur which names
contains people from Annuaire Entreprise (AE)
"""

from airflow import DAG
from enrich.config import (
    COHORTS,
    DBT,
    TASKS,
    XCOMS,
    EnrichActeursClosedConfig,
)
from enrich.tasks.airflow_logic.enrich_acteurs_closed_suggestions import (
    enrich_acteurs_closed_suggestions_task,
)
from enrich.tasks.airflow_logic.enrich_config_create_task import (
    enrich_config_create_task,
)
from enrich.tasks.airflow_logic.enrich_dbt_model_read_task import (
    enrich_dbt_model_read_task,
)
from enrich.tasks.airflow_logic.enrich_dbt_models_refresh_task import (
    enrich_dbt_models_refresh_task,
)
from shared.config import CATCHUPS, SCHEDULES, START_DATES, config_to_airflow_params

with DAG(
    dag_id="enrich_acteurs_closed",
    dag_display_name="🚪 Enrichir - Acteurs Fermés",
    default_args={
        "owner": "airflow",
        "depends_on_past": False,
        "email_on_failure": False,
        "email_on_retry": False,
        "retries": 0,
    },
    description=(
        "Un DAG pour détécter et remplacer les acteurs fermés"
        "dans l'Annuaire Entreprises (AE)"
    ),
    tags=["annuaire", "entreprises", "ae", "siren", "siret", "acteurs", "fermés"],
    schedule=SCHEDULES.NONE,
    catchup=CATCHUPS.AWLAYS_FALSE,
    start_date=START_DATES.FOR_SCHEDULE_NONE,
    params=config_to_airflow_params(
        EnrichActeursClosedConfig(
            filter_equals__acteur_statut="ACTIF",
        )
    ),
) as dag:
    """
    chain(
        enrich_config_create_task(dag),
        enrich_dbt_model_read_task(
            dag,
            task_id=TASKS.ENRICH_CLOSED_CANDIDATES,
            dbt_model_name=DBT.MARTS_ENRICH_AE_CLOSED_CANDIDATES,
            xcom_push_key=XCOMS.DF_CLOSED_CANDIDATES,
        ),
        enrich_dbt_model_read_task(
            dag,
            task_id=TASKS.ENRICH_CLOSED_REPLACED,
            dbt_model_name=DBT.MARTS_ENRICH_AE_CLOSED_REPLACED,
            xcom_push_key=XCOMS.DF_CLOSED_REPLACED,
        ),
    )
    """
    config = enrich_config_create_task(dag)
    refresh_dbt = enrich_dbt_models_refresh_task(dag)
    replaced_same_siren = enrich_dbt_model_read_task(
        dag,
        task_id=TASKS.ENRICH_CLOSED_REPLACED_SAME_SIREN,
        dbt_model_name=DBT.MARTS_ENRICH_AE_CLOSED_REPLACED_SAME_SIREN,
        xcom_push_key=XCOMS.DF_CLOSED_REPLACED_SAME_SIREN,
    )
    replaced_other_siren = enrich_dbt_model_read_task(
        dag,
        task_id=TASKS.ENRICH_CLOSED_REPLACED_OTHER_SIREN,
        dbt_model_name=DBT.MARTS_ENRICH_AE_CLOSED_REPLACED_OTHER_SIREN,
        xcom_push_key=XCOMS.DF_CLOSED_REPLACED_OTHER_SIREN,
    )
    not_replaced = enrich_dbt_model_read_task(
        dag,
        task_id=TASKS.ENRICH_CLOSED_NOT_REPLACED,
        dbt_model_name=DBT.MARTS_ENRICH_AE_CLOSED_NOT_REPLACED,
        xcom_push_key=XCOMS.DF_CLOSED_NOT_REPLACED,
    )
    suggestions_same_siren = enrich_acteurs_closed_suggestions_task(
        dag,
        task_id=TASKS.ENRICH_CLOSED_SUGGESTIONS_SAME_SIREN,
        cohort_type=COHORTS.CLOSED_REP_SAME_SIREN,
        df_xcom_key=XCOMS.DF_CLOSED_REPLACED_SAME_SIREN,
    )
    suggestions_other_siren = enrich_acteurs_closed_suggestions_task(
        dag,
        task_id=TASKS.ENRICH_CLOSED_SUGGESTIONS_OTHER_SIREN,
        cohort_type=COHORTS.CLOSED_REP_OTHER_SIREN,
        df_xcom_key=XCOMS.DF_CLOSED_REPLACED_OTHER_SIREN,
    )
    suggestions_not_replaced = enrich_acteurs_closed_suggestions_task(
        dag,
        task_id=TASKS.ENRICH_CLOSED_SUGGESTIONS_NOT_REPLACED,
        cohort_type=COHORTS.CLOSED_NOT_REPLACED,
        df_xcom_key=XCOMS.DF_CLOSED_NOT_REPLACED,
    )
    config >> refresh_dbt  # type: ignore
    refresh_dbt >> replaced_same_siren >> suggestions_same_siren  # type: ignore
    refresh_dbt >> replaced_other_siren >> suggestions_other_siren  # type: ignore
    refresh_dbt >> not_replaced >> suggestions_not_replaced  # type: ignore
