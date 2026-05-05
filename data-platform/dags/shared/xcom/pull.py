"""Single XCom pull helper, shared across DAGs.

Each DAG provides its own correspondence table mapping a lookup key to
the `(task_id, xcom_key)` it should pull from. This guarantees consistent
pulls (no typo on `key`, no wrong `task_ids`) without duplicating the
helper in every DAG.
"""

from typing import Any, Mapping

import pandas as pd
from airflow.models.taskinstance import TaskInstance
from airflow.sdk.exceptions import AirflowSkipException
from shared.xcom.models import XComSource
from shared.xcom.normalize import normalize_xcom_value
from utils import logging_utils as log


def xcom_pull(
    ti: TaskInstance,
    key: str,
    mapping: Mapping[str, XComSource],
    skip_if_empty: bool = False,
) -> Any:
    msg = f"XCOM from {ti.task_id=} pulling {key=}:"
    if key not in mapping:
        raise ValueError(f"{msg} key inconnue")

    src = mapping[key]
    value = ti.xcom_pull(key=src["xcom_key"], task_ids=src["task_id"])
    value = normalize_xcom_value(value)

    if skip_if_empty and (
        value is None or (isinstance(value, pd.DataFrame) and value.empty)
    ):
        raise AirflowSkipException(f"✋ {msg} est vide, on s'arrête là")
    log.preview(f"{msg} value = ", value)
    return value
