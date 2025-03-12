"""Task IDs for enrich anonymize people DAG"""

from dataclasses import dataclass


@dataclass(frozen=True)
class TASKS:
    READ: str = "close_acteurs_via_ae_read"
    SUGGEST: str = "close_acteurs_via_ae_suggest"
