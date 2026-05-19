import dataclasses


@dataclasses.dataclass(frozen=True)
class TASKS:
    DB_DATA_PREPARE: str = "db_data_prepare"
    DB_WRITE_TYPE_ACTION_SUGGESTIONS: str = "db_write_type_action_suggestions"
    KEEP_ACTEUR_CHANGED: str = "keep_acteur_changed"
    SOURCE_CONFIG_VALIDATE: str = "source_config_validate"
    SOURCE_DATA_DOWNLOAD: str = "source_data_download"
    SOURCE_DATA_NORMALIZE: str = "source_data_normalize"
    SOURCE_DATA_VALIDATE: str = "source_data_validate"
