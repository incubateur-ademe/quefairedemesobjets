"""Column names for RGPD anonymize DAG. Columns
are used in conf, dataframes and SQL queries. These
don't include Acteur fields (for this we stick to Acteur models)"""

from dataclasses import dataclass


@dataclass(frozen=True)
class COLS:
    # Dry run
    DRY_RUN: str = "dry_run"

    # QFDMO
    QFDMO_ACTEUR_NOMS_ORIGIN: str = "qfdmo_acteur_noms_origine"
    QFDMO_ACTEUR_NOMS_MATCH: str = "qfdmo_acteur_noms_match"
    QFDMO_ACTEUR_NOMS_COMPARISON: str = "qfdmo_acteur_noms_comparaison"
    QFDMO_ACTEUR_ID: str = "qfdmo_acteur_id"

    # Annuaire Entreprise
    AE_NOM_PREFIX: str = "ae_nom"
    AE_PRENOM_PREFIX: str = "ae_prenom"

    # Matching
    MATCH_SCORE: str = "match_score"
    MATCH_WORDS: str = "match_words"
    MATCH_THRESHOLD: str = "match_threshold"
