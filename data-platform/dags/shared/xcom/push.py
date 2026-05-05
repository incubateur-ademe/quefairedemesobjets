"""Single XCom pull helper, shared across DAGs.

Each DAG provides its own correspondence table mapping a lookup key to
the `(task_id, xcom_key)` it should pull from. This guarantees consistent
pulls (no typo on `key`, no wrong `task_ids`) without duplicating the
helper in every DAG.
"""

from typing import Any

from airflow.models.taskinstance import TaskInstance
from shared.xcom.models import XComSource


def xcom_push(
    ti: TaskInstance,
    key: str,
    value: Any,
    mapping: dict[str, XComSource],
) -> None:
    try:
        resolved_key = mapping[key]
    except KeyError:
        raise ValueError(f"Key {key} not found in XCOM_SOURCES")
    # check task_id is the same as the task_id in the resolved_key
    if resolved_key["task_id"] != ti.task_id:
        raise ValueError(f"Task ID mismatch: {resolved_key['task_id']} != {ti.task_id}")
    ti.xcom_push(key=resolved_key["xcom_key"], value=value)
