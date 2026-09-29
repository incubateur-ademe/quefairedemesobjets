"""Write the values of every key result that has a source.

PostHog key results run their insight; code key results run the function
registered here under their code; manual ones are left alone.
"""

import logging
from datetime import date
from typing import Callable

from django.db.models import Q

from qfdmo.models import ActeurStatus, DisplayedActeur
from stats.models import KeyResult, KeyResultValue
from stats.posthog import run_insight

logger = logging.getLogger(__name__)

Computation = Callable[[], dict[date, float]]

REGISTRY: dict[str, Computation] = {}

# Excluded from the SIRET/SIREN share, as in the historical Metabase query
SOURCE_CODE_EXCLUDED_FROM_SIRET_SHARE = "recyclivrebal"


def key_result(code: str):
    def decorator(fn: Computation) -> Computation:
        REGISTRY[code] = fn
        return fn

    return decorator


@key_result("part_acteurs_siret_siren")
def part_acteurs_siret_siren() -> dict[date, float]:
    acteurs = DisplayedActeur.objects.filter(statut=ActeurStatus.ACTIF).exclude(
        source__code=SOURCE_CODE_EXCLUDED_FROM_SIRET_SHARE
    )
    total = acteurs.count()
    if not total:
        return {}
    identified = acteurs.filter(
        Q(siret__regex=r"^.{5,}") | Q(siren__regex=r"^.{5,}")
    ).count()
    # Snapshot stored on the 1st of the month: the last run of the month wins.
    return {date.today().replace(day=1): identified / total}


def compute(result: KeyResult) -> dict[date, float]:
    if result.source == KeyResult.Source.POSTHOG and result.posthog_insight:
        return run_insight(result.posthog_insight)
    if result.source == KeyResult.Source.CODE and result.code in REGISTRY:
        return REGISTRY[result.code]()
    return {}


def compute_all() -> int:
    """Upsert the values of every computable key result. Returns their count.
    A failing key result is logged and skipped so the others still run."""
    count = 0
    for result in KeyResult.objects.exclude(source=KeyResult.Source.MANUAL):
        try:
            values = compute(result)
        except Exception:
            logger.exception("key result %s failed", result.code)
            continue
        KeyResultValue.objects.bulk_create(
            [
                KeyResultValue(key_result=result, date=day, value=value)
                for day, value in values.items()
            ],
            update_conflicts=True,
            unique_fields=["key_result", "date"],
            update_fields=["value"],
        )
        count += len(values)
    return count
