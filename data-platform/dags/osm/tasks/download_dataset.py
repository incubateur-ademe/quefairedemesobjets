"""Tâche Airflow qui télécharge dans un dossier temporaire le dataset OSM"""

from urllib.request import urlretrieve

from airflow.sdk import task
from tqdm import tqdm

from osm.config.models import OSMExtractLoadConfig
from utils import logging_utils as log


def task_info_get():
    return "#### Téléchargement du dataset OSM France depuis Geofrabrik.de"


@task(doc_md=task_info_get())
def download_osm_dataset_task(
    config: OSMExtractLoadConfig,
) -> str:

    with tqdm(
        unit="B",
        unit_scale=True,
        unit_divisor=1024,
        miniters=1,
        desc="Downloading OSM dataset:",
    ) as progress:
        last_bytes = 0

        def reporthook(block_num: int, block_size: int, total_size: int) -> None:
            nonlocal last_bytes
            if total_size > 0 and progress.total != total_size:
                progress.total = total_size
            downloaded = (
                min(block_num * block_size, total_size)
                if total_size > 0
                else block_num * block_size
            )
            delta = downloaded - last_bytes
            if delta > 0:
                progress.update(delta)
                last_bytes = downloaded

        dataset_tmp_path, _ = urlretrieve(
            str(config.osm_dataset_url), reporthook=reporthook
        )

    log.preview("Dataset temporary path", dataset_tmp_path)

    return dataset_tmp_path
