from airflow import DAG
from airflow.models.baseoperator import chain
from shared.config.start_dates import START_DATES
from sources.tasks.airflow_logic.db_data_prepare_task import db_data_prepare_task
from sources.tasks.airflow_logic.db_read_acteur_task import db_read_acteur_task
from sources.tasks.airflow_logic.db_write_type_action_suggestions_task import (
    db_write_type_action_suggestions_task,
    db_write_type_action_suggestions_v2_task,
)
from sources.tasks.airflow_logic.keep_acteur_changed_task import (
    keep_acteur_changed_task,
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

default_params = {
    "schedule": None,
    "max_active_runs": 1,
    "start_date": START_DATES.DEFAULT,
}


def eo_task_chain(dag: DAG) -> None:

    chain(
        source_config_validate_task(dag),
        source_data_download_task(dag),
        source_data_normalize_task(dag),
        source_data_validate_task(dag),
        db_read_acteur_task(dag),
        keep_acteur_changed_task(dag),
        db_data_prepare_task(dag),
        db_write_type_action_suggestions_task(dag),
    )


def eo_task_chain_v2(dag: DAG) -> None:

    chain(
        source_config_validate_task(dag),
        source_data_download_task(dag),
        source_data_normalize_task(dag),
        source_data_validate_task(dag),
        db_read_acteur_task(dag),
        keep_acteur_changed_task(dag),
        db_data_prepare_task(dag),
        db_write_type_action_suggestions_v2_task(dag),
    )
