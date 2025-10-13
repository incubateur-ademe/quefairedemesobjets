from airflow import DAG
from enrich.tasks.airflow_logic.db_read_acteur_cp_task import db_read_acteur_cp_task
from enrich.tasks.airflow_logic.db_write_cp_suggestions_task import (
    db_write_cp_suggestions_task,
)
from enrich.tasks.airflow_logic.normalize_acteur_cp_task import normalize_acteur_cp_task
from shared.config.start_dates import START_DATES
from shared.config.tags import TAGS

with DAG(
    dag_id="enrich_acteurs_normalize_codepostal",
    dag_display_name="🌆 Normalize - Code postal",
    default_args={
        "owner": "airflow",
        "depends_on_past": False,
        "email_on_failure": False,
        "email_on_retry": False,
        "retries": 0,
    },
    description=(
        "Un DAG pour corriger les codes postaux : vérifier qu'ils sont conformes"
        " à la norme et proposer une correction le cas échéant"
    ),
    tags=[TAGS.ENRICH, TAGS.ACTEURS, TAGS.CP],
    start_date=START_DATES.DEFAULT,
) as dag:
    db_read_acteur_cp = db_read_acteur_cp_task(dag)
    acteur_cp_normalize = normalize_acteur_cp_task(dag)
    db_write_cp_suggestions = db_write_cp_suggestions_task(dag)
    db_read_acteur_cp >> acteur_cp_normalize >> db_write_cp_suggestions  # type: ignore
