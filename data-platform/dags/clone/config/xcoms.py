"""Constants and helper for consistent XCOM pushes & pulls"""

from dataclasses import dataclass
from functools import partial

from clone.config.tasks import TASKS
from shared.xcom.pull import XComSource
from shared.xcom.pull import xcom_pull as _xcom_pull


@dataclass(frozen=True)
class XCOMS:
    CONFIG: str = "config"


XCOM_SOURCES: dict[str, XComSource] = {
    XCOMS.CONFIG: {"task_id": TASKS.CONFIG_CREATE, "xcom_key": XCOMS.CONFIG},
}


xcom_pull = partial(_xcom_pull, mapping=XCOM_SOURCES)
