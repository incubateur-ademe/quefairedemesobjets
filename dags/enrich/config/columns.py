"""Column names for RGPD anonymize DAG. Columns
are used in conf, dataframes and SQL queries. These
don't include Acteur fields (for this we stick to Acteur models)"""

from dataclasses import dataclass


@dataclass(frozen=True)
class COLS:

    # Acteurs
    ACTEUR_ID: str = "acteur_id"
    ACTEUR_TYPE_ID: str = "acteur_type_id"
    ACTEUR_TYPE_CODE: str = "acteur_type_code"
    ACTEUR_SOURCE_ID: str = "acteur_source_id"
    ACTEUR_SOURCE_CODE: str = "acteur_source_code"
    ACTEUR_SIRET: str = "acteur_siret"
    ACTEUR_NOM: str = "acteur_nom"
    ACTEUR_NOMS_ORIGINE: str = "acteur_noms_origine"
    ACTEUR_NOMS_NORMALISES: str = "acteur_noms_normalises"
    ACTEUR_COMMENTAIRES: str = "acteur_commentaires"
    ACTEUR_ADRESSE: str = "acteur_adresse"
    ACTEUR_CODE_POSTAL: str = "acteur_code_postal"
    ACTEUR_VILLE: str = "acteur_ville"
    ACTEUR_NAF: str = "acteur_naf"
    ACTEUR_LONGITUDE: str = "acteur_longitude"
    ACTEUR_LATITUDE: str = "acteur_latitude"

    # Annuaire Entreprise
    AE_DIRIGEANTS_NOMS: str = "ae_dirigeants_noms_prenoms"

    # Suggestions
    SUGGEST_COHORT_CODE: str = "suggestion_cohorte_code"
    SUGGEST_COHORT_LABEL: str = "suggestion_cohorte_label"

    # Replacements
    REMPLACER_SIRET: str = "remplacer_siret"
    REMPLACER_NOM: str = "remplacer_nom"
    REMPLACER_ADRESSE: str = "remplacer_adresse"
    REMPLACER_CODE_POSTAL: str = "remplacer_code_postal"
    REMPLACER_VILLE: str = "remplacer_ville"
    REMPLACER_NAF: str = "remplacer_naf"

    # Matching
    MATCH_WORDS: str = "match_words"
    MATCH_SCORE: str = "match_score"
