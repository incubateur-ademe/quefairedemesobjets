"""Constants and helpers to configure XCom for Crawl DAG,
so we are more reliable & concise in our XCOM usage
(so easy to typo a key or pull from wrong task and Airflow
happily gives None without complaining)"""

from dataclasses import dataclass
from typing import Any

import pandas as pd
from airflow.exceptions import AirflowSkipException
from airflow.models.taskinstance import TaskInstance
from enrich.config.tasks import TASKS
from utils import logging_utils as log


@dataclass(frozen=True)
class XCOMS:
    CONFIG: str = "config"

    DF_CLOSED_REPLACED_SAME_SIREN: str = "df_acteurs_closed_replaced_same_siren"
    DF_CLOSED_REPLACED_OTHER_SIREN: str = "df_acteurs_closed_replaced_other_siren"
    DF_CLOSED_NOT_REPLACED_UNITE: str = "df_acteurs_closed_not_replaced_unite"
    DF_CLOSED_NOT_REPLACED_ETABLISSEMENT: str = (
        "df_acteurs_closed_not_replaced_etablissement"
    )

    DF_READ: str = "df_read"
    DF_MATCH: str = "df_match"

    DB_READ_ACTEUR_CP: str = "db_read_acteur_cp"
    DB_READ_REVISION_ACTEUR_CP: str = "db_read_revision_acteur_cp"
    NORMALIZED_ACTEUR_CP: str = "normalized_acteur_cp"
    NORMALIZED_REVISION_ACTEUR_CP: str = "normalized_revision_acteur_cp"


def xcom_pull(ti: TaskInstance, key: str, skip_if_empty: bool = False) -> Any:
    """For pulls, we create a helper to constrain keys
    to specific task ids to guarantee consistent pulls"""

    # Init
    msg = f"XCOM from {ti.task_id=} pulling {key=}:"  # For logging

    # Reading values
    if key == XCOMS.CONFIG:
        value = ti.xcom_pull(key=key, task_ids=TASKS.CONFIG_CREATE)
    elif key == XCOMS.DF_CLOSED_REPLACED_SAME_SIREN:
        value = ti.xcom_pull(key=key, task_ids=TASKS.ENRICH_CLOSED_REPLACED_SAME_SIREN)
    elif key == XCOMS.DF_CLOSED_REPLACED_OTHER_SIREN:
        value = ti.xcom_pull(key=key, task_ids=TASKS.ENRICH_CLOSED_REPLACED_OTHER_SIREN)
    elif key == XCOMS.DF_CLOSED_NOT_REPLACED_UNITE:
        value = ti.xcom_pull(key=key, task_ids=TASKS.ENRICH_CLOSED_NOT_REPLACED_UNITE)
    elif key == XCOMS.DF_CLOSED_NOT_REPLACED_ETABLISSEMENT:
        value = ti.xcom_pull(
            key=key, task_ids=TASKS.ENRICH_CLOSED_NOT_REPLACED_ETABLISSEMENT
        )
    else:
        raise ValueError(f"{msg} key inconnue")

    # Skip if empty
    if skip_if_empty and (
        value is None or (isinstance(value, pd.DataFrame) and value.empty)
    ):
        raise AirflowSkipException(f"✋ {msg} est vide, on s'arrête là")

    # Logging
    log.preview(f"{msg} value = ", value)

    return value


# We don't have an helper for xcom_push because
# it can be done via the TaskInstance easily
# as ti.xcom_push(key=..., value=...)
# and we don't neet to align keys with task ids
# (task id is automatically that of the pushing task)
