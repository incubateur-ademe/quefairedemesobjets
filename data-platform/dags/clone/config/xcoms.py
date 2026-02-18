"""Constants and helper for consistent XCOM pushes & pulls"""

from dataclasses import dataclass
from typing import Any

from airflow.models.taskinstance import TaskInstance
from clone.config.tasks import TASKS
from utils import logging_utils as log


@dataclass(frozen=True)
class XCOMS:
    CONFIG: str = "config"


def xcom_pull(ti: TaskInstance, key: str) -> Any:
    """For pulls, we create a helper to constrain keys
    to specific task ids to guarantee consistent pulls"""
    msg = f"XCOM from {ti.task_id=} pulling {key=}:"  # For logging
    if key == XCOMS.CONFIG:
        value = ti.xcom_pull(key=key, task_ids=TASKS.CONFIG_CREATE)
    else:
        raise ValueError(f"{msg} key inconnue")

    log.preview(f"{msg} value = ", value)
    return value
