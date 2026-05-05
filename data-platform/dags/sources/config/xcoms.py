"""Constants and helper for consistent XCOM pushes & pulls in Sources DAG"""

from dataclasses import dataclass
from functools import partial

from shared.xcom.models import XComSource
from shared.xcom.pull import xcom_pull as _xcom_pull
from shared.xcom.push import xcom_push as _xcom_push
from sources.config.tasks import TASKS


@dataclass(frozen=True)
class XCOMS:
    # source_data_download return value (DataFrame)
    SOURCE_DOWNLOADED: str = "source_downloaded"

    # source_data_normalize
    SOURCE_NORMALIZED: str = "source_normalized"  # return value (DataFrame)
    METADATA: str = "metadata"
    DF_LOG_ERROR: str = "df_log_error"
    DF_LOG_WARNING: str = "df_log_warning"

    # keep_acteur_changed
    DF_ACTEUR_FROM_SOURCE: str = "df_acteur_from_source"
    DF_ACTEUR_FROM_DB: str = "df_acteur_from_db"
    METADATA_COLUMNS_UPDATED: str = "metadata_columns_updated"

    # db_data_prepare
    TABLE_NAME_CREATE: str = "table_name_create"
    TABLE_NAME_UPDATE: str = "table_name_update"
    TABLE_NAME_DELETE: str = "table_name_delete"
    METADATA_TO_CREATE: str = "metadata_to_create"
    METADATA_TO_UPDATE: str = "metadata_to_update"
    METADATA_TO_DELETE: str = "metadata_to_delete"

    # db_write_type_action_suggestions
    SKIP: str = "skip"


XCOM_SOURCES: dict[str, XComSource] = {
    XCOMS.SOURCE_DOWNLOADED: {
        "task_id": TASKS.SOURCE_DATA_DOWNLOAD,
        "xcom_key": "return_value",
    },
    XCOMS.SOURCE_NORMALIZED: {
        "task_id": TASKS.SOURCE_DATA_NORMALIZE,
        "xcom_key": "return_value",
    },
    XCOMS.METADATA: {
        "task_id": TASKS.SOURCE_DATA_NORMALIZE,
        "xcom_key": XCOMS.METADATA,
    },
    XCOMS.DF_LOG_ERROR: {
        "task_id": TASKS.SOURCE_DATA_NORMALIZE,
        "xcom_key": XCOMS.DF_LOG_ERROR,
    },
    XCOMS.DF_LOG_WARNING: {
        "task_id": TASKS.SOURCE_DATA_NORMALIZE,
        "xcom_key": XCOMS.DF_LOG_WARNING,
    },
    XCOMS.DF_ACTEUR_FROM_SOURCE: {
        "task_id": TASKS.KEEP_ACTEUR_CHANGED,
        "xcom_key": XCOMS.DF_ACTEUR_FROM_SOURCE,
    },
    XCOMS.DF_ACTEUR_FROM_DB: {
        "task_id": TASKS.KEEP_ACTEUR_CHANGED,
        "xcom_key": XCOMS.DF_ACTEUR_FROM_DB,
    },
    XCOMS.METADATA_COLUMNS_UPDATED: {
        "task_id": TASKS.KEEP_ACTEUR_CHANGED,
        "xcom_key": XCOMS.METADATA_COLUMNS_UPDATED,
    },
    XCOMS.TABLE_NAME_CREATE: {
        "task_id": TASKS.DB_DATA_PREPARE,
        "xcom_key": XCOMS.TABLE_NAME_CREATE,
    },
    XCOMS.TABLE_NAME_UPDATE: {
        "task_id": TASKS.DB_DATA_PREPARE,
        "xcom_key": XCOMS.TABLE_NAME_UPDATE,
    },
    XCOMS.TABLE_NAME_DELETE: {
        "task_id": TASKS.DB_DATA_PREPARE,
        "xcom_key": XCOMS.TABLE_NAME_DELETE,
    },
    XCOMS.METADATA_TO_CREATE: {
        "task_id": TASKS.DB_DATA_PREPARE,
        "xcom_key": XCOMS.METADATA_TO_CREATE,
    },
    XCOMS.METADATA_TO_UPDATE: {
        "task_id": TASKS.DB_DATA_PREPARE,
        "xcom_key": XCOMS.METADATA_TO_UPDATE,
    },
    XCOMS.METADATA_TO_DELETE: {
        "task_id": TASKS.DB_DATA_PREPARE,
        "xcom_key": XCOMS.METADATA_TO_DELETE,
    },
    XCOMS.SKIP: {
        "task_id": TASKS.DB_WRITE_TYPE_ACTION_SUGGESTIONS,
        "xcom_key": XCOMS.SKIP,
    },
}


xcom_pull = partial(_xcom_pull, mapping=XCOM_SOURCES)
xcom_push = partial(_xcom_push, mapping=XCOM_SOURCES)
