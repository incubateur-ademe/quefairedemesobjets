"""Column names for RGPD anonymize DAG. Columns
are used in conf, dataframes and SQL queries. These
don't include Acteur fields (for this we stick to Acteur models)"""

from dataclasses import dataclass


@dataclass(frozen=True)
class COLS:
    # Dry run
    DRY_RUN: str = "dry_run"

    # COMMON
    SIREN: str = "siren"

    # QFDMO
    ACTEUR_ID: str = "acteur_id"
    ACTEUR_NOMS_ORIGINE: str = "acteur_noms_origine"
    ACTEUR_NOMS_NORMALISES: str = "acteur_noms_normalises"
    ACTEUR_COMMENTAIRES: str = "acteur_commentaires"

    # Annuaire Entreprise
    AE_DIRIGEANTS_NOMS: str = "ae_dirigeants_noms_prenoms"

    # Matching
    MATCH_SCORE_AE_RGPD: str = "match_score"
    MATCH_WORDS: str = "match_words"
    MATCH_THRESHOLD: str = "match_threshold"
