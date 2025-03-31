import pytest

from dags.enrich.config.models import EnrichClosedConfig


class TestEnrichClosedConfig:

    @pytest.fixture
    def config(self):
        return EnrichClosedConfig(
            dry_run=True,
            filter_contains__commentaires="commentaires",
            filter_contains__nom="nom",
            filter_contains__naf=None,
            filter_equals__statut="ACTIF",
        )

    def test_filters_contain(self, config):
        assert config.filters_contains() == [
            {"field": "commentaires", "value": "commentaires"},
            {"field": "nom", "value": "nom"},
            {"field": "naf", "value": None},
        ]

    def test_filters_equals(self, config):
        assert config.filters_equals() == [
            {"field": "statut", "value": "ACTIF"},
        ]
