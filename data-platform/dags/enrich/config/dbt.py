"""DBT models used in the enrich DAGs"""

from dataclasses import dataclass


@dataclass(frozen=True)
class DBT:
    # RGPD
    MARTS_ENRICH_RGPD_SUGGESTIONS: str = "marts_enrich_acteurs_rgpd_suggest"

    # Closed
    MARTS_ENRICH_AE_CLOSED_CANDIDATES: str = "marts_enrich_acteurs_closed_candidates"
    MARTS_ENRICH_AE_CLOSED_REPLACED_SAME_SIREN: str = (
        "marts_enrich_acteurs_closed_suggest_replaced_same_siren"
    )
    MARTS_ENRICH_AE_CLOSED_REPLACED_OTHER_SIREN: str = (
        "marts_enrich_acteurs_closed_suggest_replaced_other_siren"
    )
    MARTS_ENRICH_AE_CLOSED_NOT_REPLACED_UNITE: str = (
        "marts_enrich_acteurs_closed_suggest_not_replaced_unite"
    )
    MARTS_ENRICH_AE_CLOSED_NOT_REPLACED_ETABLISSEMENT: str = (
        "marts_enrich_acteurs_closed_suggest_not_replaced_etablissement"
    )
    MARTS_ENRICH_VILLES_TYPO: str = "marts_enrich_acteurs_villes_suggest_typo"
    MARTS_ENRICH_VILLES_NEW: str = "marts_enrich_acteurs_villes_suggest_new"
