"""DBT models used in the enrich DAGs"""

from dataclasses import dataclass


@dataclass(frozen=True)
class DBT:
    MARTS_ENRICH_AE_CLOSED_CANDIDATES: str = "marts_enrich_acteurs_closed_candidates"
    MARTS_ENRICH_AE_CLOSED_REPLACED_SAME_SIREN: str = (
        "marts_enrich_acteurs_closed_suggest_replaced_same_siren"
    )
    MARTS_ENRICH_AE_CLOSED_REPLACED_OTHER_SIREN: str = (
        "marts_enrich_acteurs_closed_suggest_replaced_other_siren"
    )
    MARTS_ENRICH_AE_CLOSED_NOT_REPLACED: str = (
        "marts_enrich_acteurs_closed_suggest_not_replaced"
    )
    MARTS_ENRICH_ACTEURS_VILLES_TYPO: str = "marts_enrich_acteurs_villes_suggest_typo"
    MARTS_ENRICH_ACTEURS_VILLES_NEW: str = "marts_enrich_acteurs_villes_suggest_new"
