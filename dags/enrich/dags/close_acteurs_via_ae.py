"""
DAG to anonymize QFDMO acteur which names
contains people from Annuaire Entreprise (AE)
"""

from datetime import datetime

from airflow import DAG
from airflow.models.baseoperator import chain
from airflow.models.param import Param
from enrich.config import COLS
from enrich.tasks.airflow_logic.close_acteurs_via_ae_read_task import (
    close_acteurs_via_ae_read_task,
)
from enrich.tasks.airflow_logic.close_acteurs_via_ae_suggest_task import (
    close_acteurs_via_ae_suggest_task,
)

with DAG(
    dag_id="close_acteurs_via_ae",
    dag_display_name="Acteurs - Fermer via Annuaire Entreprise (AE)",
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
        "Un DAG pour fermer les acteurs"
        "dont les unités légales/établissement sont fermés"
        "dans l'Annuaire Entreprise (AE)"
    ),
    tags=["annuaire", "entreprise", "ae", "siren", "siret", "acteurs"],
    params={
        COLS.DRY_RUN: Param(
            True,
            type="boolean",
            description_md="🚱 Si coché, aucune tâche d'écriture ne sera effectuée",
        ),
    },
    schedule=None,
    catchup=False,
) as dag:
    chain(
        close_acteurs_via_ae_read_task(dag),
        close_acteurs_via_ae_suggest_task(dag),
    )
