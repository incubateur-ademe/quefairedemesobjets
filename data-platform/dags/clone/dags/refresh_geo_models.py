"""DAG to refresh DBT models needed for enrich DAGs"""

import logging

from acteurs.tasks.airflow_logic.check_model_table_consistency_task import (
    check_model_table_consistency_task,
)
from acteurs.tasks.airflow_logic.replace_acteur_table_task import (
    replace_acteur_table_task,
)
from airflow.decorators import dag
from airflow.operators.bash import BashOperator
from airflow.sdk.bases.operator import chain
from shared.config.airflow import DEFAULT_ARGS
from shared.config.dag_names import REFRESH_GEO_MODELS_DAG_ID
from shared.config.dbt_commands import DBT_RUN, DBT_TEST
from shared.config.start_dates import START_DATES
from shared.config.tags import TAGS

logger = logging.getLogger(__name__)


@dag(
    dag_id=REFRESH_GEO_MODELS_DAG_ID,
    dag_display_name="🔄 Rafraichir - Modèles Géographiques (EPCI)",
    default_args=DEFAULT_ARGS,
    description=(
        "Un DAG pour rafraîchir les modèles Géo via DBT après le clonage des données"
        " de `la poste` et `Koumoul EPCI` et `INSEE Commune`"
    ),
    tags=[TAGS.ENRICH, TAGS.CLONE, TAGS.LAPOSTE, TAGS.KOUMOUL, TAGS.EPCI, TAGS.DBT],
    schedule=None,
    start_date=START_DATES.DEFAULT,
    params={},
    max_active_runs=1,
)
def refresh_geo_models():
    dbt_run_exposure_acteurs_common = BashOperator(
        task_id="dbt_run_exposure_acteurs_common",
        bash_command=f"{DBT_RUN} tag:geo",
    )
    dbt_test_exposure_acteurs_common = BashOperator(
        task_id="dbt_test_exposure_acteurs_common",
        bash_command=f"{DBT_TEST} tag:geo",
    )
    check_model_table_epci_task = check_model_table_consistency_task(
        "qfdmo", "EPCI", "exposure_epci"
    )
    replace_epci_table_task = replace_acteur_table_task(
        "qfdmo_", "exposure_", tables=["epci"]
    )

    chain(
        dbt_run_exposure_acteurs_common,
        dbt_test_exposure_acteurs_common,
        check_model_table_epci_task,
        replace_epci_table_task,
    )


dag = refresh_geo_models()
