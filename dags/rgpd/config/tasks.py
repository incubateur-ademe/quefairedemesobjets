"""Task IDs for RGPD anonymize people DAG"""

from dataclasses import dataclass


@dataclass(frozen=True)
class TASKS:
    READ: str = "rgpd_anonymize_people_read"
    MATCH_SCORE: str = "rgpd_anonymize_people_match"
    SUGGEST: str = "rgpd_anonymize_people_suggest"
