"""Task IDs for RGPD anonymize people DAG"""

from dataclasses import dataclass


@dataclass(frozen=True)
class TASKS:
    READ: str = "enrich_ae_rgpd_read"
    MATCH_SCORE: str = "enrich_ae_rgpd_match"
    SUGGEST: str = "enrich_ae_rgpd_suggest"
