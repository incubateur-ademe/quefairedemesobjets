from datetime import datetime

from airflow import DAG
from airflow.models.baseoperator import chain
from sources.tasks.airflow_logic.compute_link_tables_task import (
    compute_link_tables_task,
)
from sources.tasks.airflow_logic.db_data_prepare_task import db_data_prepare_task
from sources.tasks.airflow_logic.db_read_acteur_task import db_read_acteur_task
from sources.tasks.airflow_logic.db_write_type_action_suggestions_task import (
    db_write_type_action_suggestions_task,
)
from sources.tasks.airflow_logic.filter_acteur_toupdate_task import (
    filter_acteur_toupdate_task,
)
from sources.tasks.airflow_logic.propose_acteur_changes_task import (
    propose_acteur_changes_task,
)
from sources.tasks.airflow_logic.source_config_validate_task import (
    source_config_validate_task,
)
from sources.tasks.airflow_logic.source_data_download_task import (
    source_data_download_task,
)
from sources.tasks.airflow_logic.source_data_normalize_task import (
    source_data_normalize_task,
)
from sources.tasks.airflow_logic.source_data_validate_task import (
    source_data_validate_task,
)

default_args = {
    "owner": "airflow",
    "depends_on_past": False,
    "start_date": datetime(2024, 3, 23),
    "email_on_failure": False,
    "email_on_retry": False,
    "retries": 1,
}


def eo_task_chain(dag: DAG) -> None:

    chain(
        source_config_validate_task(dag),
        source_data_download_task(dag),
        source_data_normalize_task(dag),
        source_data_validate_task(dag),
        db_read_acteur_task(dag),
        filter_acteur_toupdate_task(dag),
        propose_acteur_changes_task(dag),
        compute_link_tables_task(dag),
        db_data_prepare_task(dag),
        db_write_type_action_suggestions_task(dag),
    )
