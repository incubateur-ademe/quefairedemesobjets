"""Column names for enrich anonymize DAG. Columns
are used in conf, dataframes and SQL queries. These
don't include Acteur fields (for this we stick to Acteur models)"""

from dataclasses import dataclass


@dataclass(frozen=True)
class COLS:
    # Dry run
    DRY_RUN: str = "dry_run"

    # QFDMO
    QFDMO_ACTEUR_NOMS: str = "qfdmo_acteur_noms"
    QFDMO_ACTEUR_ID: str = "qfdmo_acteur_id"

    # ANNUAIRE ENTREPRISE
    AE_UNITE_STATUS: str = "ae_etatAdministratifUniteLegale"
    AE_ETAB_STATUS: str = "ae_etatAdministratifEtablissement"
