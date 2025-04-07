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
    ACTEUR_SIRET: str = "acteur_siret"
    ACTEUR_NOM: str = "acteur_nom"
    ACTEUR_NOMS_ORIGINE: str = "acteur_noms_origine"
    ACTEUR_NOMS_NORMALISES: str = "acteur_noms_normalises"
    ACTEUR_COMMENTAIRES: str = "acteur_commentaires"

    # Annuaire Entreprise
    AE_DIRIGEANTS_NOMS: str = "ae_dirigeants_noms_prenoms"
    REMPLACER_SIRET: str = "remplacer_siret"
    REMPLACER_NOM: str = "remplacer_nom"
    REMPLACER_COHORTE: str = "remplacer_cohorte"

    # Fields identical between acteurs and remplacements
    # hence replacer_ prefix not present on the model column names
    REMPLACER_ADRESSE: str = "adresse"
    REMPLACER_CODE_POSTAL: str = "code_postal"
    REMPLACER_VILLE: str = "ville"
    REMPLACER_NAF: str = "naf"

    # Matching
    MATCH_SCORE_AE_RGPD: str = "match_score"
    MATCH_WORDS: str = "match_words"
    MATCH_THRESHOLD: str = "match_threshold"
