"""Task IDs for Replicate Annuaire Entreprise (AE) DAG"""

from dataclasses import dataclass


@dataclass(frozen=True)
class TASKS:
    CONFIG_CREATE = "clone_config_create"
    TABLE_CREATE = "clone_table_create"
    TABLE_VALIDATE = "clone_table_validate"
    VIEW_IN_USE_SWITCH = "clone_view_in_use_switch"
    OLD_TABLES_REMOVE = "clone_old_tables_remove"
