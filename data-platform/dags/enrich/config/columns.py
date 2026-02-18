"""Column names enrichment DAGs"""

from dataclasses import dataclass

# All values we want to suggest via our enrichment DBT models
# should start with this prefix
SUGGEST_PREFIX = "suggest"


@dataclass(frozen=True)
class COLS:

    # Acteurs
    ACTEUR_ID: str = "acteur_id"
    ACTEUR_ID_EXTERNE: str = "acteur_id_externe"
    ACTEUR_TYPE_ID: str = "acteur_type_id"
    ACTEUR_SOURCE_ID: str = "acteur_source_id"
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
    ACTEUR_STATUT: str = "acteur_statut"
    # Annuaire Entreprise
    AE_DIRIGEANTS_NOMS: str = "ae_dirigeants_noms_prenoms"

    # Suggestions

    # Replacements
    SUGGEST_SIRET: str = "suggest_siret"
    SUGGEST_NOM: str = "suggest_nom"
    SUGGEST_ADRESSE: str = "suggest_adresse"
    SUGGEST_CODE_POSTAL: str = "suggest_code_postal"
    SUGGEST_VILLE: str = "suggest_ville"
    SUGGEST_NAF: str = "suggest_naf"

    # Suggestions
    SUGGEST_COHORT: str = f"{SUGGEST_PREFIX}_cohort"
    SUGGEST_SIRET: str = f"{SUGGEST_PREFIX}_siret"
    SUGGEST_SIREN: str = f"{SUGGEST_PREFIX}_siren"
    SUGGEST_NOM: str = f"{SUGGEST_PREFIX}_nom"
    SUGGEST_ADRESSE: str = f"{SUGGEST_PREFIX}_adresse"
    SUGGEST_CODE_POSTAL: str = f"{SUGGEST_PREFIX}_code_postal"
    SUGGEST_VILLE: str = f"{SUGGEST_PREFIX}_ville"
    SUGGEST_NAF: str = f"{SUGGEST_PREFIX}_naf_principal"
    SUGGEST_LONGITUDE: str = f"{SUGGEST_PREFIX}_longitude"
    SUGGEST_LATITUDE: str = f"{SUGGEST_PREFIX}_latitude"
    SUGGEST_ACTEUR_TYPE_ID: str = f"{SUGGEST_PREFIX}_acteur_type_id"

    # Matching
    MATCH_WORDS: str = "match_words"
    MATCH_SCORE: str = "match_score"
    MATCH_THRESHOLD: str = "match_threshold"
