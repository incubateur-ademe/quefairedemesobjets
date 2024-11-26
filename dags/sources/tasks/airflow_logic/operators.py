from datetime import datetime

from airflow import DAG
from airflow.models.baseoperator import chain
from shared.tasks.airflow_logic.write_data_task import write_data_task
from sources.tasks.airflow_logic.db_data_prepare_task import db_data_prepare_task
from sources.tasks.airflow_logic.db_read_acteur_task import db_read_acteur_task
from sources.tasks.airflow_logic.db_read_propositions_max_id_task import (
    db_read_propositions_max_id_task,
)
from sources.tasks.airflow_logic.propose_acteur_changes_task import (
    propose_acteur_changes_task,
)
from sources.tasks.airflow_logic.propose_acteur_services_task import (
    propose_acteur_services_task,
)
from sources.tasks.airflow_logic.propose_acteur_to_delete_task import (
    propose_acteur_to_delete_task,
)
from sources.tasks.airflow_logic.propose_labels_task import propose_labels_task
from sources.tasks.airflow_logic.propose_services_sous_categories_task import (
    propose_services_sous_categories_task,
)
from sources.tasks.airflow_logic.propose_services_task import propose_services_task
from sources.tasks.airflow_logic.read_mapping_from_postgres_task import (
    read_mapping_from_postgres_task,
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
    read_tasks = [
        read_mapping_from_postgres_task(
            dag=dag, table_name="qfdmo_acteurtype", task_id="db_read_acteurtype"
        ),
        read_mapping_from_postgres_task(
            dag=dag, table_name="qfdmo_source", task_id="db_read_source"
        ),
        read_mapping_from_postgres_task(
            dag=dag, table_name="qfdmo_action", task_id="db_read_action"
        ),
        read_mapping_from_postgres_task(
            dag=dag, table_name="qfdmo_acteurservice", task_id="db_read_acteurservice"
        ),
        read_mapping_from_postgres_task(
            dag=dag, table_name="qfdmo_labelqualite", task_id="db_read_labelqualite"
        ),
        read_mapping_from_postgres_task(
            dag=dag,
            table_name="qfdmo_souscategorieobjet",
            task_id="db_read_souscategorieobjet",
        ),
        db_read_propositions_max_id_task(dag),
    ]

    create_tasks = [
        propose_services_task(dag),
        propose_labels_task(dag),
        propose_acteur_services_task(dag),
    ]

    chain(
        source_config_validate_task(dag),
        source_data_download_task(dag),
        source_data_normalize_task(dag),
        source_data_validate_task(dag),
        read_tasks,
        db_read_acteur_task(dag),
        propose_acteur_changes_task(dag),
        propose_acteur_to_delete_task(dag),
        create_tasks,
        propose_services_sous_categories_task(dag),
        db_data_prepare_task(dag),
        write_data_task(dag),
    )
