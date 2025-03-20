"""Task IDs for Replicate Annuaire Entreprise (AE) DAG"""

from dataclasses import dataclass


@dataclass(frozen=True)
class TASKS:
    TABLE_NAMES_PREP = "clone_ae_table_name_prepare"
    TABLE_CREATE_UNITE = "clone_ae_table_create_unite_legale"
    TABLE_CREATE_ETAB = "clone_ae_table_create_etablissement"
    TABLE_VALIDATE_UNITE = "clone_ae_table_validate_unite_legale"
    TABLE_VALIDATE_ETAB = "clone_ae_table_validate_etablissement"
    VIEWS_SWITCH = "clone_ae_view_in_use_switch"
    TABLES_OLD_REMOVE = "clone_ae_old_tables_remove"
    TABLES_OLD_REMOVE_VALIDATE = "clone_ae_old_tables_remove_validate"
