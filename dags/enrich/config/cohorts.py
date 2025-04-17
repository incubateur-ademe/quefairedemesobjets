"""Cohorts for enrich DAGs"""

from dataclasses import dataclass

INTRO = "🚪 Acteurs Fermés:"


@dataclass(frozen=True)
class Cohort:
    code: str
    label: str


@dataclass(frozen=True)
class COHORTS:
    CLOSED_NOT_REPLACED: Cohort = Cohort(
        code="acteurs_closed_not_replaced",
        label=f"{INTRO} 🔴 non remplacés",
    )
    CLOSED_REP_OTHER_SIREN: Cohort = Cohort(
        code="acteurs_closed_replaced_other_siren",
        label=f"{INTRO} 🟡 remplacés par SIRET d'un autre SIREN",
    )
    CLOSED_REP_SAME_SIREN: Cohort = Cohort(
        code="acteurs_closed_replaced_same_siren",
        label=f"{INTRO} 🟢 remplacés par SIRET du même SIREN",
    )

    ACTEURS_VILLES_TYPO: Cohort = Cohort(
        code="acteurs_villes_variation_ortographe",
        label="🌆 Changement de ville: 🟢 variation d'ortographe",
    )
    ACTEURS_VILLES_NEW: Cohort = Cohort(
        code="acteurs_villes_anciennes_nouvelles",
        label="🌆 Changement de ville: 🟡 ancienne -> nouvelle",
    )
