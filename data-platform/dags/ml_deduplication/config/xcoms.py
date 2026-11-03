"""Constants and helpers to configure XCom for ML-deduplication DAG"""

from dataclasses import dataclass
from functools import partial

from ml_deduplication.config.tasks import TASKS
from shared.xcom.models import XComSource
from shared.xcom.pull import xcom_pull as _xcom_pull
from shared.xcom.push import xcom_push as _xcom_push


@dataclass(frozen=True)
class XCOMS:
    CONFIG: str = "config"
    RUN_ID: str = "run_id"
    ACTEURS_VIEW: str = "acteurs_view"
    DF_CLUSTERS_SELECT: str = "df_clusters_select"
    DF_PARENTS_CHOOSE_NEW: str = "df_parents_choose_new"
    DF_PARENTS_CHOOSE_DATA: str = "df_parents_choose_data"
    SUGGESTIONS_WORKING: str = "suggestions_working"
    SUGGESTIONS_FAILING: str = "suggestions_failing"


XCOM_SOURCES: dict[str, XComSource] = {
    XCOMS.CONFIG: {"task_id": TASKS.CONFIG_CREATE, "xcom_key": XCOMS.CONFIG},
    XCOMS.RUN_ID: {"task_id": TASKS.CONFIG_CREATE, "xcom_key": XCOMS.RUN_ID},
    XCOMS.ACTEURS_VIEW: {
        "task_id": TASKS.SELECTION,
        "xcom_key": XCOMS.ACTEURS_VIEW,
    },
    XCOMS.DF_CLUSTERS_SELECT: {
        "task_id": TASKS.CLUSTERS_SELECT,
        "xcom_key": XCOMS.DF_CLUSTERS_SELECT,
    },
    XCOMS.DF_PARENTS_CHOOSE_NEW: {
        "task_id": TASKS.PARENTS_CHOOSE_NEW,
        "xcom_key": XCOMS.DF_PARENTS_CHOOSE_NEW,
    },
    XCOMS.DF_PARENTS_CHOOSE_DATA: {
        "task_id": TASKS.PARENTS_CHOOSE_DATA,
        "xcom_key": XCOMS.DF_PARENTS_CHOOSE_DATA,
    },
    XCOMS.SUGGESTIONS_WORKING: {
        "task_id": TASKS.SUGGESTIONS_PREPARE,
        "xcom_key": XCOMS.SUGGESTIONS_WORKING,
    },
    XCOMS.SUGGESTIONS_FAILING: {
        "task_id": TASKS.SUGGESTIONS_PREPARE,
        "xcom_key": XCOMS.SUGGESTIONS_FAILING,
    },
}


xcom_pull = partial(_xcom_pull, mapping=XCOM_SOURCES)

xcom_push = partial(_xcom_push, mapping=XCOM_SOURCES)
