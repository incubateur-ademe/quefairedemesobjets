"""Constants and helpers to configure XCom for Crawl DAG,
so we are more reliable & concise in our XCOM usage
(so easy to typo a key or pull from wrong task and Airflow
happily gives None without complaining)"""

from dataclasses import dataclass
from typing import Any

import pandas as pd
from airflow.exceptions import AirflowSkipException
from airflow.models.taskinstance import TaskInstance
from crawl.config.tasks import TASKS
from utils import logging_utils as log


@dataclass(frozen=True)
class XCOMS:
    # Input dataframes
    DF_READ: str = "df_read"

    # Check dataframes
    DF_SYNTAX_OK: str = "df_syntax_ok"
    DF_SYNTAX_FAIL: str = "df_syntax_fail"
    DF_DNS_OK: str = "df_dns_ok"
    DF_DNS_FAIL: str = "df_dns_fail"
    DF_CRAWL_DIFF_STANDARD: str = "df_crawl_diff_standard"
    DF_CRAWL_DIFF_OTHER: str = "df_crawl_diff_other"
    DF_CRAWL_FAIL: str = "df_crawl_fail"

    # Suggestions: metadata & preparation dicts
    SUGGEST_META: str = "suggestions_metadata"
    SUGGEST_SYNTAX_FAIL: str = "suggestions_syntax_fail"
    SUGGEST_DNS_FAIL: str = "suggestions_dns_fail"
    SUGGEST_CRAWL_DIFF_STANDARD: str = "suggestions_crawl_diff_standard"
    SUGGEST_CRAWL_DIFF_OTHER: str = "suggestions_crawl_diff_other"


def xcom_pull(ti: TaskInstance, key: str, skip_if_empty: bool = False) -> Any:
    """For pulls, we create a helper to constrain keys
    to specific task ids to guarantee consistent pulls"""
    value = None
    msg = f"XCOM from {ti.task_id=} pulling {key=}:"  # For logging
    if key == XCOMS.DF_READ:
        value = ti.xcom_pull(key=key, task_ids=TASKS.READ)
    elif key == XCOMS.DF_SYNTAX_OK:
        value = ti.xcom_pull(key=key, task_ids=TASKS.CHECK_SYNTAX)
    elif key == XCOMS.DF_SYNTAX_FAIL:
        value = ti.xcom_pull(key=key, task_ids=TASKS.CHECK_SYNTAX)
    elif key == XCOMS.DF_DNS_OK:
        value = ti.xcom_pull(key=key, task_ids=TASKS.CHECK_DNS)
    elif key == XCOMS.DF_DNS_FAIL:
        value = ti.xcom_pull(key=key, task_ids=TASKS.CHECK_DNS)
    elif key == XCOMS.DF_CRAWL_DIFF_STANDARD:
        value = ti.xcom_pull(key=key, task_ids=TASKS.CHECK_CRAWL)
    elif key == XCOMS.DF_CRAWL_DIFF_OTHER:
        value = ti.xcom_pull(key=key, task_ids=TASKS.CHECK_CRAWL)
    elif key == XCOMS.DF_CRAWL_FAIL:
        value = ti.xcom_pull(key=key, task_ids=TASKS.CHECK_CRAWL)
    else:
        raise ValueError(f"{msg} key inconnue")

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
