"""
DAG to anonymize QFDMO acteur which names
contains people from Annuaire Entreprise (AE)
"""

import re

from airflow import DAG
from airflow.models.baseoperator import chain
from airflow.operators.bash import BashOperator
from airflow.utils.trigger_rule import TriggerRule
from enrich.config import EnrichDbtModelsRefreshConfig
from shared.config import CATCHUPS, SCHEDULES, START_DATES, config_to_airflow_params

with DAG(
    dag_id="enrich_dbt_models_refresh",
    dag_display_name="🔄 Enrichir - Rafraîchir les modèles DBT",
    default_args={
        "owner": "airflow",
        "depends_on_past": False,
        "email_on_failure": False,
        "email_on_retry": False,
        "retries": 0,
    },
    description=(
        "Un DAG pour rafraîchir les modèles DBT nécessaires"
        "à l'enrichissement des acteurs"
    ),
    tags=["dbt", "annuaire", "entreprises", "ae", "ban", "marts"],
    schedule=SCHEDULES.DAILY,
    catchup=CATCHUPS.AWLAYS_FALSE,
    start_date=START_DATES.YESTERDAY,
    params=config_to_airflow_params(
        EnrichDbtModelsRefreshConfig(
            dbt_models_refresh_commands=[
                "dbt build --select +int_ae_unite_legale",
                "dbt build --select +int_ae_etablissement",
                "dbt build --select +int_ban_adresses",
                "dbt build --select int_ban_villes",
            ],
        )
    ),
) as dag:
    tasks = []
    for cmd in dag.params.get("dbt_models_refresh_commands", []):
        cmd = cmd.strip()
        if not cmd:
            continue
        cmd_id = re.sub(r"__+", "_", re.sub(r"[^a-zA-Z0-9]+", "_", cmd))
        cmd += " --debug --threads 1"
        tasks.append(
            BashOperator(
                task_id=f"enrich_{cmd_id}",
                bash_command=cmd,
                trigger_rule=TriggerRule.ALL_DONE,
            )
        )
    chain(*tasks)
