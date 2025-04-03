"""
DAG to anonymize QFDMO acteur which names
contains people from Annuaire Entreprise (AE)
"""

from datetime import datetime

from airflow import DAG
from airflow.models.baseoperator import chain
from airflow.models.param import Param
from enrich.config import COLS
from enrich.tasks.airflow_logic.enrich_ae_rgpd_match_task import (
    enrich_ae_rgpd_match_task,
)
from enrich.tasks.airflow_logic.enrich_ae_rgpd_read_task import (
    enrich_ae_rgpd_read_task,
)
from enrich.tasks.airflow_logic.enrich_ae_rgpd_suggest_task import (
    enrich_ae_rgpd_suggest_task,
)

with DAG(
    dag_id="enrich_ae_acteurs_rgpd",
    dag_display_name="Enrichir - AE - Acteurs RGPD",
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
        "Un DAG pour anonymiser les acteurs QFDMO dont"
        "le nom contient des personnes de l'Annuaire Entreprise (AE)"
    ),
    tags=["enrich", "annuaire", "entreprise", "siren", "ae", "acteurs"],
    params={
        COLS.DRY_RUN: Param(
            True,
            type="boolean",
            description_md="🚱 Si coché, aucune tâche d'écriture ne sera effectuée",
        ),
        "filter_comments_contain": Param(
            "",
            type=["null", "string"],
            description_md="🔍 Filtre sur les commentaires pour la lecture des données",
        ),
        COLS.MATCH_THRESHOLD: Param(
            1,
            type="number",
            minimum=0.5,
            maximum=1,
            description_md=r"""🎯 Seuil de match pour considérer un acteur
            anonymisable:
             - **match** = ratio du nombre de mots du nom de l'acteur qui correspondent
            à des mots de nom/prénom des personnes de l'AE
             - **minimum** = 0.5
             - **maximum** = 1
            """,
        ),
    },
    schedule=None,
    catchup=False,
) as dag:
    chain(
        enrich_ae_rgpd_read_task(dag),
        enrich_ae_rgpd_match_task(dag),
        enrich_ae_rgpd_suggest_task(dag),
    )
