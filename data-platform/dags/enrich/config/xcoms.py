"""Constants and helpers to configure XCom for Enrich DAG,
so we are more reliable & concise in our XCOM usage
(so easy to typo a key or pull from wrong task and Airflow
happily gives None without complaining)"""

from dataclasses import dataclass
from functools import partial

from enrich.config.tasks import TASKS
from shared.xcom.pull import XComSource
from shared.xcom.pull import xcom_pull as _xcom_pull


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


XCOM_SOURCES: dict[str, XComSource] = {
    XCOMS.CONFIG: {"task_id": TASKS.CONFIG_CREATE, "xcom_key": XCOMS.CONFIG},
    XCOMS.DF_CLOSED_REPLACED_SAME_SIREN: {
        "task_id": TASKS.ENRICH_CLOSED_REPLACED_SAME_SIREN,
        "xcom_key": XCOMS.DF_CLOSED_REPLACED_SAME_SIREN,
    },
    XCOMS.DF_CLOSED_REPLACED_OTHER_SIREN: {
        "task_id": TASKS.ENRICH_CLOSED_REPLACED_OTHER_SIREN,
        "xcom_key": XCOMS.DF_CLOSED_REPLACED_OTHER_SIREN,
    },
    XCOMS.DF_CLOSED_NOT_REPLACED_UNITE: {
        "task_id": TASKS.ENRICH_CLOSED_NOT_REPLACED_UNITE,
        "xcom_key": XCOMS.DF_CLOSED_NOT_REPLACED_UNITE,
    },
    XCOMS.DF_CLOSED_NOT_REPLACED_ETABLISSEMENT: {
        "task_id": TASKS.ENRICH_CLOSED_NOT_REPLACED_ETABLISSEMENT,
        "xcom_key": XCOMS.DF_CLOSED_NOT_REPLACED_ETABLISSEMENT,
    },
    XCOMS.DB_READ_ACTEUR_CP: {
        "task_id": TASKS.DB_READ_ACTEUR_CP,
        "xcom_key": XCOMS.DB_READ_ACTEUR_CP,
    },
    XCOMS.DB_READ_REVISION_ACTEUR_CP: {
        "task_id": TASKS.DB_READ_ACTEUR_CP,
        "xcom_key": XCOMS.DB_READ_REVISION_ACTEUR_CP,
    },
    XCOMS.NORMALIZED_ACTEUR_CP: {
        "task_id": TASKS.NORMALIZE_ACTEUR_CP,
        "xcom_key": XCOMS.NORMALIZED_ACTEUR_CP,
    },
    XCOMS.NORMALIZED_REVISION_ACTEUR_CP: {
        "task_id": TASKS.NORMALIZE_ACTEUR_CP,
        "xcom_key": XCOMS.NORMALIZED_REVISION_ACTEUR_CP,
    },
}


xcom_pull = partial(_xcom_pull, mapping=XCOM_SOURCES)


# We don't have an helper for xcom_push because
# it can be done via the TaskInstance easily
# as ti.xcom_push(key=..., value=...)
# and we don't neet to align keys with task ids
# (task id is automatically that of the pushing task)
