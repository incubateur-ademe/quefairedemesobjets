"""
DAG to anonymize QFDMO acteur which names
contains people from Annuaire Entreprise (AE)
"""

from datetime import datetime

from airflow import DAG
from airflow.models.baseoperator import chain
from airflow.models.param import Param
from enrich.tasks.airflow_logic.enrich_read_ae_closed_candidates_task import (
    enrich_read_ae_closed_candidates_task,
)

with DAG(
    dag_id="enrich_ae_closed",
    dag_display_name="Enrichir - AE - Acteurs fermés",
    default_args={
        "owner": "airflow",
        "depends_on_past": False,
        "start_date": datetime(2025, 3, 5),
        "catchup": False,
        "email_on_failure": False,
        "email_on_retry": False,
        "retries": 0,
    },
    description=(
        "Un DAG pour détécter et remplacer les acteurs fermés"
        "dans l'Annuaire Entreprises (AE)"
    ),
    tags=["annuaire", "entreprise", "ae", "siren", "siret", "acteurs"],
    schedule=None,
    catchup=False,
    params={
        "dry_run": Param(
            True,
            type="boolean",
            description_md="🚱 Si coché, aucune tâche d'écriture ne sera effectuée",
        ),
    },
) as dag:
    chain(
        enrich_read_ae_closed_candidates_task(dag),
    )
