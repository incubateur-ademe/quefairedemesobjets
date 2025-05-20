"""DAG to refresh DBT models needed for enrich DAGs"""

import logging
import re

from airflow import DAG
from airflow.models.baseoperator import chain
from airflow.operators.bash import BashOperator
from airflow.utils.trigger_rule import TriggerRule
from enrich.config.models import EnrichDbtModelsRefreshConfig
from shared.config.catchups import CATCHUPS
from shared.config.models import config_to_airflow_params
from shared.config.schedules import SCHEDULES
from shared.config.start_dates import START_DATES
from shared.config.tags import TAGS

logger = logging.getLogger(__name__)

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
    tags=[TAGS.ENRICH, TAGS.ANNAIRE_ENTREPRISE, TAGS.BAN, TAGS.PREPARE, TAGS.DBT],
    schedule=SCHEDULES.DAILY,
    catchup=CATCHUPS.AWLAYS_FALSE,
    start_date=START_DATES.YESTERDAY,
    params=config_to_airflow_params(
        EnrichDbtModelsRefreshConfig(
            dbt_models_refresh_commands=[
                "dbt build --select +tag:intermediate,tag:ae",
                "dbt build --select +tag:intermediate,tag:ban",
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
        logger.info(f"Create bash operator with command: {cmd}")
        tasks.append(
            BashOperator(
                task_id=f"enrich_{cmd_id}",
                bash_command=cmd,
                trigger_rule=TriggerRule.ALL_DONE,
            )
        )
    chain(*tasks)
