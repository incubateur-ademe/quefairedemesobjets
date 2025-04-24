"""Cohorts for enrich DAGs"""

from dataclasses import dataclass


@dataclass(frozen=True)
class COHORTS:
    CLOSED_NOT_REPLACED = "🚪 Acteurs Fermés: 🔴 non remplacés"
    CLOSED_REP_OTHER_SIREN = (
        "🚪 Acteurs Fermés: 🟡 remplacés par SIRET d'un autre SIREN"
    )
    CLOSED_REP_SAME_SIREN = "🚪 Acteurs Fermés: 🟢 remplacés par SIRET du même SIREN"
    RGPD = "Anonymisation RGPD"
