"""Display thresholds and ordering for autocomplete results.

The modelsearch postgres backend annotates every result with two floats:

- ``_fuzzy_raw_similarity``: trigram similarity with no bonus. Decides
  *whether* a result is shown.
- ``_fuzzy_similarity``: the ranking score (title-length normalisation and
  prefix boost applied). Decides *where* a result is shown.

The backend already drops rows below ``RAW_SIMILARITY_MINIMUM`` in SQL, so
``admits`` only has to arbitrate the band between minimum and sufficient.
"""

from dataclasses import dataclass
from typing import Iterable, TypeVar

from django.conf import settings

Result = TypeVar("Result")


@dataclass(frozen=True)
class DisplayThresholds:
    raw_similarity_minimum: float
    raw_similarity_sufficient: float
    score_minimum: float

    @classmethod
    def from_settings(cls) -> "DisplayThresholds":
        values = settings.SEARCH_DISPLAY_THRESHOLDS
        return cls(
            raw_similarity_minimum=values["RAW_SIMILARITY_MINIMUM"],
            raw_similarity_sufficient=values["RAW_SIMILARITY_SUFFICIENT"],
            score_minimum=values["SCORE_MINIMUM"],
        )

    def admits(self, result) -> bool:
        raw, score = result._fuzzy_raw_similarity, result._fuzzy_similarity
        if raw < self.raw_similarity_minimum:
            return False
        return raw >= self.raw_similarity_sufficient or score >= self.score_minimum


def ranked_by_similarity(
    results: Iterable[Result], thresholds: DisplayThresholds, limit: int
) -> list[Result]:
    """Results admitted by ``thresholds``, best raw similarity first, score
    as tie-breaker, capped at ``limit``. Non-mutating."""
    admitted = (result for result in results if thresholds.admits(result))
    return sorted(
        admitted,
        key=lambda result: (result._fuzzy_raw_similarity, result._fuzzy_similarity),
        reverse=True,
    )[:limit]
