"""Tâche Airflow qui télécharge dans un dossier temporaire le dataset OSM"""

import math
import time
from pathlib import Path
from tempfile import TemporaryDirectory
from urllib.request import urlretrieve

from airflow.sdk import task
from osm.config.models import OSMExtractLoadConfig
from utils import logging_utils as log


def task_info_get():
    return "#### Téléchargement du dataset OSM France depuis Geofrabrik.de"


@task(doc_md=task_info_get())
def download_osm_dataset_task(
    config: OSMExtractLoadConfig,
) -> str:
    logger = log.logger_get()
    start_time = time.time()
    url = str(config.osm_dataset_url)

    last_pct = None

    def reporthook(block_num: int, block_size: int, total_size: int) -> None:
        nonlocal last_pct
        downloaded = (
            min(block_num * block_size, total_size)
            if total_size > 0
            else block_num * block_size
        )
        if total_size > 0:
            pct = math.floor(100 * downloaded / total_size)
            if pct != last_pct and pct % 10 == 0:
                last_pct = pct
                logger.info(log.progress_string(downloaded, total_size))

    logger.info(f"⬇️ Downloading OSM dataset from {url}")
    with TemporaryDirectory(prefix="osm_dag", delete=False) as tmp_dir:
        dataset_tmp_path, _ = urlretrieve(
            url, filename=Path(tmp_dir) / "dataset.osm.pbf", reporthook=reporthook
        )

    elapsed = time.time() - start_time
    logger.info(
        log.banner_string(
            f"✅ Dataset downloaded: {url}\n"
            f"📁 Path: {dataset_tmp_path} ({math.ceil(elapsed)}s)"
        )
    )

    return str(dataset_tmp_path)
