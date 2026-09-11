from types import SimpleNamespace

import pytest
from django.test import override_settings

from search.ranking import DisplayThresholds, ranked_by_similarity

THRESHOLDS = DisplayThresholds(
    raw_similarity_minimum=0.5, raw_similarity_sufficient=0.75, score_minimum=1.2
)


def result(raw, score, name=""):
    return SimpleNamespace(
        _fuzzy_raw_similarity=raw, _fuzzy_similarity=score, name=name
    )


class TestDisplayThresholdsAdmits:
    def test_rejects_below_minimum_even_with_high_score(self):
        assert not THRESHOLDS.admits(result(raw=0.49, score=5.0))

    def test_admits_at_or_above_sufficient_regardless_of_score(self):
        assert THRESHOLDS.admits(result(raw=0.75, score=0.0))

    def test_in_between_band_requires_score_minimum(self):
        assert THRESHOLDS.admits(result(raw=0.5, score=1.2))
        assert not THRESHOLDS.admits(result(raw=0.74, score=1.19))

    def test_from_settings_reads_django_settings(self):
        with override_settings(
            SEARCH_DISPLAY_THRESHOLDS={
                "RAW_SIMILARITY_MINIMUM": 0.1,
                "RAW_SIMILARITY_SUFFICIENT": 0.2,
                "SCORE_MINIMUM": 0.3,
            }
        ):
            assert DisplayThresholds.from_settings() == DisplayThresholds(0.1, 0.2, 0.3)


class TestRankedBySimilarity:
    def test_orders_by_raw_then_score_and_caps_at_limit(self):
        results = [
            result(0.8, 0.9, "raw-high-score-low"),
            result(0.6, 1.5, "band-admitted"),
            result(0.8, 1.4, "raw-high-score-high"),
            result(0.6, 1.0, "band-rejected"),
            result(1.0, 0.5, "exact"),
        ]
        ranked = ranked_by_similarity(results, THRESHOLDS, limit=3)
        assert [r.name for r in ranked] == [
            "exact",
            "raw-high-score-high",
            "raw-high-score-low",
        ]

    def test_does_not_mutate_input(self):
        results = [result(0.6, 2.0), result(0.9, 0.1)]
        snapshot = list(results)
        ranked_by_similarity(results, THRESHOLDS, limit=10)
        assert results == snapshot

    @pytest.mark.parametrize("limit", [0, 1])
    def test_limit_is_respected(self, limit):
        results = [result(0.9, 1.0), result(0.8, 1.0)]
        assert len(ranked_by_similarity(results, THRESHOLDS, limit=limit)) == limit
