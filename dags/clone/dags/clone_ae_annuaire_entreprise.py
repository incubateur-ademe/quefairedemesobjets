"""
DAG to clone the Annuaire Entreprise in our DB.
"AE" stands for "Annuaire Entreprise" to prevent
running into DB table name length limits.
"""

from datetime import datetime

from airflow import DAG
from airflow.models.baseoperator import chain
from airflow.models.param import Param
from clone.tasks.airflow_logic.clone_ae_table_create_etab_task import (
    clone_ea_table_create_etab_task,
)
from clone.tasks.airflow_logic.clone_ae_table_create_unite_task import (
    clone_ea_table_create_unite_task,
)
from clone.tasks.airflow_logic.clone_ae_table_names_prepare_task import (
    clone_ea_table_names_prepare_task,
)
from clone.tasks.airflow_logic.clone_ae_table_validate_etab_task import (
    clone_ea_table_validate_etab_task,
)
from clone.tasks.airflow_logic.clone_ae_table_validate_unite_task import (
    clone_ea_table_validate_unite_task,
)
from clone.tasks.airflow_logic.clone_ae_tables_old_remove_task import (
    clone_ea_tables_old_remove_task,
)
from clone.tasks.airflow_logic.clone_ae_views_in_use_switch_task import (
    clone_ea_views_in_use_switch_task,
)

with DAG(
    dag_id="clone_ae_annuaire_entreprise",
    dag_display_name="Cloner - Annuaire Entreprise (AE)",
    default_args={
        "owner": "airflow",
        "depends_on_past": False,
        "start_date": datetime(2025, 3, 5),
        "catchup": False,
        "email_on_failure": False,
        "email_on_retry": False,
        "retries": 0,
    },
    description=("Un DAG pour répliquer l'Annuaire Entreprise (AE) dans notre DB"),
    tags=["clone", "annuaire", "entreprise", "siret", "siren", "ae"],
    params={
        "dry_run": Param(
            False,
            type="boolean",
            description_md="🚱 Si coché, aucune tâche d'écriture ne sera effectuée",
        ),
    },
    schedule=None,
    catchup=False,
) as dag:
    chain(
        clone_ea_table_names_prepare_task(dag),
        clone_ea_table_create_unite_task(dag),
        clone_ea_table_create_etab_task(dag),
        clone_ea_table_validate_unite_task(dag),
        clone_ea_table_validate_etab_task(dag),
        clone_ea_views_in_use_switch_task(dag),
        clone_ea_tables_old_remove_task(dag),
    )
