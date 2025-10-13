"""
Flow Prefect to clone BAN's adresses table in our DB.
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
    name="Cloner - BAN - Adresses",
    description=(
        "Clone la table 'adresses' de la Base Adresse Nationale (BAN) dans notre DB"
    ),
)
def clone_ban_adresses(
    dry_run: bool = False,
    table_kind: str = "ban_adresses",
    data_endpoint: str = (
        "https://adresse.data.gouv.fr/data/ban/adresses/latest/csv/"
        "adresses-france.csv.gz"
    ),
    clone_method: Literal[
        "download_to_disk_first", "stream_directly"
    ] = "stream_directly",
    file_downloaded: str = "adresses-france.csv.gz",
    file_unpacked: str = "adresses-france.csv",
    delimiter: str = ",",
) -> None:
    """
    Flow Prefect pour cloner la table AE etablissement.

    Args:
    Args:
        dry_run: 🚱 if True, no write task will be performed
        table_kind: 📊 The type of table to create
        data_endpoint: 📥 URL to download the data
        clone_method: 📥 Method to create the table
        file_downloaded: 📦 Name of the downloaded file
        file_unpacked: 📦 Name of the unpacked file
        delimiter: 🔤 Delimiter used in the file
    """
    log.info("Démarrage du flow clone_ban_adresses")
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
    table_created = create_table.submit(config)
    table_validated = validate_table.submit(config, wait_for=[table_created])
    view_switched = switch_view.submit(config, wait_for=[table_validated])
    remove_old_tables.submit(config, wait_for=[view_switched])


# if __name__ == "__main__":
#     clone_ban_adresses(dry_run=True)
