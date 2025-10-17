"""
Flow prefect to clone AE's unite_legale table in our DB.
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
    name="Cloner - AE - Unite Legale",
    description=(
        "Clone la table 'unite_legale' de l'Annuaire Entreprises (AE) dans notre DB"
    ),
)
def clone_ae_unite_legale(
    dry_run: bool = False,
    table_kind: str = "ae_unite_legale",
    data_endpoint: str = (
        "https://object.files.data.gouv.fr/data-pipeline-open/siren/stock/"
        "StockUniteLegale_utf8.zip"
    ),
    clone_method: Literal[
        "download_to_disk_first", "stream_directly"
    ] = "stream_directly",
    file_downloaded: str = "StockUniteLegale_utf8.zip",
    file_unpacked: str = "StockUniteLegale_utf8.csv",
    delimiter: str = ",",
) -> None:
    """
    Flow Prefect pour cloner la table AE unite_legale.

    Args:
        dry_run: 🚱 if True, no write task will be performed
        table_kind: 📊 The type of table to create
        data_endpoint: 📥 URL to download the data
        clone_method: 📥 Method to create the table
        file_downloaded: 📦 Name of the downloaded file
        file_unpacked: 📦 Name of the unpacked file
        delimiter: 🔤 Delimiter used in the file
    """
    log.info("Démarrage du flow clone_ae_unite_legale")
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
#     clone_ae_unite_legale(dry_run=True)
