"""Cohorts for enrich DAGs"""

from dataclasses import dataclass

INTRO = "🚪 Acteurs Fermés:"


@dataclass(frozen=True)
class COHORTS:
    CLOSED_NOT_REPLACED: str = f"{INTRO} 🔴 non remplacés"
    CLOSED_REP_OTHER_SIREN: str = f"{INTRO} 🟡 remplacés par SIRET d'un autre SIREN"
    CLOSED_REP_SAME_SIREN: str = f"{INTRO} 🟢 remplacés par SIRET du même SIREN"
