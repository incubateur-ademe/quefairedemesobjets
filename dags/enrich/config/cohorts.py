"""Cohorts for enrich DAGs"""

from dataclasses import dataclass

CLOSED = "🚪 Acteurs Fermés:"


@dataclass(frozen=True)
class COHORTS:
    CLOSED_NOT_REPLACED = f"{CLOSED} 🔴 non remplacés"
    CLOSED_REP_OTHER_SIREN = f"{CLOSED} 🟡 remplacés par SIRET d'un autre SIREN"
    CLOSED_REP_SAME_SIREN = f"{CLOSED} 🟢 remplacés par SIRET du même SIREN"
