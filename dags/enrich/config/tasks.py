"""Task IDs for RGPD anonymize people DAG"""

from dataclasses import dataclass


@dataclass(frozen=True)
class TASKS:
    # Read tasks
    READ_AE_RGPD: str = "enrich_ae_rgpd_read"
    READ_AE_CLOSED_CANDIDATES: str = "enrich_read_ae_closed_candidates"
    READ_AE_CLOSED_REPLACED: str = "enrich_read_ae_closed_replaced"

    # Matching tasks
    MATCH_SCORE_AE_RGPD: str = "enrich_ae_rgpd_match"

    # Suggestion tasks
    SUGGEST_AE_RGPD: str = "enrich_ae_rgpd_suggest"
