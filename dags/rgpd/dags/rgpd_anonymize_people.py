"""
DAG to anonymize QFDMO acteur which names
contains people from Annuaire Entreprise (AE)
"""

from datetime import datetime

from airflow import DAG
from airflow.models.baseoperator import chain
from airflow.models.param import Param
from rgpd.config import COLS
from rgpd.tasks.airflow_logic.rgpd_anonymize_people_match_task import (
    rgpd_anonymize_people_match_task,
)
from rgpd.tasks.airflow_logic.rgpd_anonymize_people_read_task import (
    rgpd_anonymize_people_read_task,
)
from rgpd.tasks.airflow_logic.rgpd_anonymize_people_suggest_task import (
    rgpd_anonymize_people_suggest_task,
)

FILTER_COMMENTS_CONTAIN_DEFAULT = (
    "source changee le 18-07-2024. Ancienne source CMA non-reparActeur. "
    "Nouvelle source : LVAO"
)

with DAG(
    dag_id="rgpd_anonymize_people",
    dag_display_name="RGPD - Anonymiser les personnes acteurs",
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
    tags=["rgpd", "annuaire", "entreprise", "siren", "ae", "acteurs"],
    params={
        COLS.DRY_RUN: Param(
            True,
            type="boolean",
            description_md="🚱 Si coché, aucune tâche d'écriture ne sera effectuée",
        ),
        "filter_comments_contain": Param(
            FILTER_COMMENTS_CONTAIN_DEFAULT,
            type="string",
            description_md="🔍 Filtre sur les commentaires pour la lecture des données",
        ),
        COLS.MATCH_THRESHOLD: Param(
            1,
            type="number",
            description_md=r"""🎯 Seuil de match pour considérer un acteur
            anonymisable.
             - **match** = ratio du nombre de mots du nom de l'acteur qui correspondent
            à des mots de nom/prénom des personnes de l'AE
             - **threshold** = contrainte en dur de ==1 pour la v1
            """,
        ),
    },
    schedule=None,
    catchup=False,
) as dag:
    chain(
        rgpd_anonymize_people_read_task(dag),
        rgpd_anonymize_people_match_task(dag),
        rgpd_anonymize_people_suggest_task(dag),
    )
