"""
Flow Prefect to clone AE's etablissement table in our DB.
"""

from typing import Literal

from prefect import flow

from data_platform.clone.business_logic.clone_config_create import create_config
from data_platform.clone.business_logic.clone_old_tables_remove import remove_old_tables
from data_platform.clone.business_logic.clone_table_create import create_table
from data_platform.clone.business_logic.clone_table_validate import validate_table
from data_platform.clone.business_logic.clone_view_in_use_switch import switch_view
from data_platform.shared.utils import logging_utils as log


@flow(
    name="Cloner - External - Table",
    description="Clone une table externe dans la DB warehouse",
)
def clone_external_table(
    dry_run: bool = False,
    table_kind: str = "external_table",
    data_endpoint: str = "https://endpoint.com/table.csv",
    clone_method: Literal[
        "download_to_disk_first", "stream_directly"
    ] = "stream_directly",
    file_downloaded: str = "table.csv.zip",
    file_unpacked: str = "table.csv",
    delimiter: str = ",",
) -> None:
    """
    Flow Prefect to clone an external table in the warehouse DB.

    Args:
        dry_run: 🚱 if True, no write task will be performed
        table_kind: 📊 The type of table to create
        data_endpoint: 📥 URL to download the data
        clone_method: 📥 Method to create the table
        file_downloaded: 📦 Name of the downloaded file
        file_unpacked: 📦 Name of the unpacked file
        delimiter: 🔤 Delimiter used in the file
    """
    log.info("Démarrage du flow clone_external_table")
    # Enchaînement des tâches
    config = create_config(
        dry_run=dry_run,
        table_kind=table_kind,
        data_endpoint=data_endpoint,
        clone_method=clone_method,
        file_downloaded=file_downloaded,
        file_unpacked=file_unpacked,
        delimiter=delimiter,
    )
    # a = task_a.submit()
    table_created = create_table(config)
    table_validated = validate_table(config, wait_for=[table_created])
    view_switched = switch_view(config, wait_for=[table_validated])
    remove_old_tables(config, wait_for=[view_switched])


# if __name__ == "__main__":
#     clone_ae_etablissement(dry_run=True)
