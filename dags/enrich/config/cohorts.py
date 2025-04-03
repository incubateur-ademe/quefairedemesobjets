"""Cohorts for enrich DAGs"""

from dataclasses import dataclass

INTRO = "🚪 Acteurs Fermés:"


@dataclass(frozen=True)
class COHORTS:
    ACTEURS_CLOSED_NOT_REPLACED: str = f"{INTRO} 🔴 non remplacés"
    ACTEURS_CLOSED_REP_DIFF_SIREN: str = f"{INTRO} 🟡 remplacés via SIREN diff"
    ACTEURS_CLOSED_REP_SAME_SIREN: str = f"{INTRO} 🟢 remplacés via SIREN idem"
