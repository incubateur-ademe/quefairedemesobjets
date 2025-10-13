from typing import Literal

import pendulum
from prefect import task

from data_platform.clone.config.model import CloneConfig
from data_platform.shared.utils import logging_utils as log


@task(name="Créer la configuration")
def create_config(
    dry_run: bool,
    table_kind: str,
    data_endpoint: str,
    clone_method: Literal["download_to_disk_first", "stream_directly"],
    file_downloaded: str,
    file_unpacked: str,
    delimiter: str,
) -> CloneConfig:
    """
    💡 Quoi: création de la config du flow
    🎯 Pourquoi: réutilisation à travers tout le flow
    🏗️ Comment: modèle pydantic qui valide et génère une config
    """
    params = {
        "dry_run": dry_run,
        "table_kind": table_kind,
        "data_endpoint": data_endpoint,
        "clone_method": clone_method,
        "file_downloaded": file_downloaded,
        "file_unpacked": file_unpacked,
        "delimiter": delimiter,
    }
    config = clone_config_create(params)
    log.info(f"Configuration générée: {config.model_dump()}")
    return config


def clone_config_create(params: dict) -> CloneConfig:
    """All core config logic should be validated with Pydantic
    + unit tests. What's left here is validation we don't want to
    impose on tests (e.g. file existence)"""
    extra = {"run_timestamp": pendulum.now("UTC").strftime("%Y%m%d%H%M%S")}
    config = CloneConfig(**(params | extra))
    config.validate_paths()
    return config
