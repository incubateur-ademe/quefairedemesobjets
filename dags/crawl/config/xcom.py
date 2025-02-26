"""Constants and helpers to configure XCom for Crawl DAG,
so we are more reliable & concise in our XCOM usage"""

from typing import Any

from airflow.models.taskinstance import TaskInstance
from crawl.config import tasks as TASKS

XCOM_DF_READ = "df_read"
XCOM_DF_SYNTAX_OK = "df_syntax_ok"
XCOM_DF_SYNTAX_FAIL = "df_syntax_fail"
XCOM_DF_DNS_OK = "df_dns_ok"
XCOM_DF_DNS_FAIL = "df_dns_fail"
XCOM_DF_URLS_OK_SAME = "df_urls_ok_same"
XCOM_DF_URLS_OK_DIFF = "df_urls_ok_diff"
XCOM_DF_URLS_FAIL = "df_urls_fail"
XCOM_SUGGESTIONS_META = "suggestions_metadata"
XCOM_SUGGESTIONS_CTX = "suggestions_context"
XCOM_SUGGESTIONS_PREP = "suggestions"


def xcom_pull(ti: TaskInstance, key: str) -> Any:
    """For pulls, we create a helper to constrain keys
    to specific task ids to guarantee consistent pulls"""
    if key == XCOM_DF_READ:
        return ti.xcom_pull(key=key, task_ids=TASKS.READ)
    elif key == XCOM_DF_SYNTAX_OK:
        return ti.xcom_pull(key=key, task_ids=TASKS.CHECK_SYNTAX)
    elif key == XCOM_DF_SYNTAX_FAIL:
        return ti.xcom_pull(key=key, task_ids=TASKS.CHECK_SYNTAX)
    elif key == XCOM_DF_DNS_OK:
        return ti.xcom_pull(key=key, task_ids=TASKS.CHECK_DNS)
    elif key == XCOM_DF_DNS_FAIL:
        return ti.xcom_pull(key=key, task_ids=TASKS.CHECK_DNS)
    elif key == XCOM_DF_URLS_OK_SAME:
        return ti.xcom_pull(key=key, task_ids=TASKS.CHECK_URLS)
    elif key == XCOM_DF_URLS_OK_DIFF:
        return ti.xcom_pull(key=key, task_ids=TASKS.CHECK_URLS)
    elif key == XCOM_DF_URLS_FAIL:
        return ti.xcom_pull(key=key, task_ids=TASKS.CHECK_URLS)
    elif key == XCOM_SUGGESTIONS_META:
        return ti.xcom_pull(key=key, task_ids=TASKS.SUGGESTIONS_META)
    elif key == XCOM_SUGGESTIONS_PREP:
        return ti.xcom_pull(key=key, task_ids=TASKS.SUGGESTIONS_PREP)
    else:
        raise ValueError(f"xcom_pull: unknown key {key}")


# We don't have an helper for xcom_push because
# it can be done via the TaskInstance easily
# as ti.xcom_push(key=..., value=...)
# and we don't neet to align keys with task ids
# (task id is automatically that of the pushing task)
