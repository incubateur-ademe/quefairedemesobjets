"""Constants and helpers to configure XCom for Clustering DAG"""

from dataclasses import dataclass
from typing import Any

import pandas as pd
from airflow.exceptions import AirflowSkipException
from airflow.models.taskinstance import TaskInstance
from cluster.config.tasks import TASKS
from utils import logging_utils as log


@dataclass(frozen=True)
class XCOMS:
    CONFIG: str = "config"
    DF_READ: str = "df_read"
    DF_NORMALIZE: str = "df_normalize"
    DF_CLUSTERS_PREPARE: str = "df_clusters_prepare"
    DF_PARENTS_CHOOSE_NEW: str = "df_parents_choose_new"
    DF_PARENTS_CHOOSE_DATA: str = "df_parents_choose_data"
    SUGGESTIONS_WORKING: str = "suggestions_working"
    SUGGESTIONS_FAILING: str = "suggestions_failing"


def xcom_pull(ti: TaskInstance, key: str, skip_if_empty: bool = False) -> Any:
    """For pulls, we create a helper to constrain keys
    to specific task ids to guarantee consistent pulls"""
    value: Any = None  # type: ignore
    msg = f"XCOM from {ti.task_id=} pulling {key=}:"  # For logging
    if key == XCOMS.CONFIG:
        value = ti.xcom_pull(key=key, task_ids=TASKS.CONFIG_CREATE)
    elif key == XCOMS.DF_READ:
        value = ti.xcom_pull(key=key, task_ids=TASKS.SELECTION)
    elif key == XCOMS.DF_NORMALIZE:
        value = ti.xcom_pull(key=key, task_ids=TASKS.NORMALIZE)
    elif key == XCOMS.DF_CLUSTERS_PREPARE:
        value = ti.xcom_pull(key=key, task_ids=TASKS.CLUSTERS_PREPARE)
    elif key == XCOMS.DF_PARENTS_CHOOSE_NEW:
        value = ti.xcom_pull(key=key, task_ids=TASKS.PARENTS_CHOOSE_NEW)
    elif key == XCOMS.DF_PARENTS_CHOOSE_DATA:
        value = ti.xcom_pull(key=key, task_ids=TASKS.PARENTS_CHOOSE_DATA)
    elif key == XCOMS.SUGGESTIONS_WORKING:
        value = ti.xcom_pull(key=key, task_ids=TASKS.SUGGESTIONS_PREPARE)
    elif key == XCOMS.SUGGESTIONS_FAILING:
        value = ti.xcom_pull(key=key, task_ids=TASKS.SUGGESTIONS_PREPARE)
    else:
        raise ValueError(f"{msg}: key inconnue")

    if skip_if_empty and (
        value is None or (isinstance(value, pd.DataFrame) and value.empty)
    ):
        raise AirflowSkipException(f"✋ {msg} est vide, on s'arrête là")
    log.preview(f"{msg} value = ", value)
    return value


# We don't have an helper for xcom_push because
# it can be done via the TaskInstance easily
# as ti.xcom_push(key=..., value=...)
# and we don't neet to align keys with task ids
# (task id is automatically that of the pushing task)
