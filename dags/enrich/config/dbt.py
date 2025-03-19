"""DBT models used in the enrich DAGs"""

from dataclasses import dataclass


@dataclass(frozen=True)
class DBT:
    MARTS_ENRICH_AE_RGPD: str = "marts_enrich_ae_rgpd"
