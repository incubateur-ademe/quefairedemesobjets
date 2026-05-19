"""Constants and helpers to configure XCom for Crawl DAG,
so we are more reliable & concise in our XCOM usage
(so easy to typo a key or pull from wrong task and Airflow
happily gives None without complaining)"""

from dataclasses import dataclass
from functools import partial

from crawl.config.tasks import TASKS
from shared.xcom.models import XComSource
from shared.xcom.pull import xcom_pull as _xcom_pull
from shared.xcom.push import xcom_push as _xcom_push


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


XCOM_SOURCES: dict[str, XComSource] = {
    XCOMS.DF_READ: {"task_id": TASKS.READ, "xcom_key": XCOMS.DF_READ},
    XCOMS.DF_SYNTAX_OK: {"task_id": TASKS.CHECK_SYNTAX, "xcom_key": XCOMS.DF_SYNTAX_OK},
    XCOMS.DF_SYNTAX_FAIL: {
        "task_id": TASKS.CHECK_SYNTAX,
        "xcom_key": XCOMS.DF_SYNTAX_FAIL,
    },
    XCOMS.DF_DNS_OK: {"task_id": TASKS.CHECK_DNS, "xcom_key": XCOMS.DF_DNS_OK},
    XCOMS.DF_DNS_FAIL: {"task_id": TASKS.CHECK_DNS, "xcom_key": XCOMS.DF_DNS_FAIL},
    XCOMS.DF_CRAWL_DIFF_STANDARD: {
        "task_id": TASKS.CHECK_CRAWL,
        "xcom_key": XCOMS.DF_CRAWL_DIFF_STANDARD,
    },
    XCOMS.DF_CRAWL_DIFF_OTHER: {
        "task_id": TASKS.CHECK_CRAWL,
        "xcom_key": XCOMS.DF_CRAWL_DIFF_OTHER,
    },
    XCOMS.DF_CRAWL_FAIL: {
        "task_id": TASKS.CHECK_CRAWL,
        "xcom_key": XCOMS.DF_CRAWL_FAIL,
    },
}


xcom_pull = partial(_xcom_pull, mapping=XCOM_SOURCES)

xcom_push = partial(_xcom_push, mapping=XCOM_SOURCES)
