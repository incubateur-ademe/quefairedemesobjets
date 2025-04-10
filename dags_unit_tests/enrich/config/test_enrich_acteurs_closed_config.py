import pytest
from enrich.config.models import EnrichActeursClosedConfig


class TestEnrichClosedConfig:

    @pytest.fixture
    def config(self):
        return EnrichActeursClosedConfig(
            dry_run=True,
            filter_contains__acteur_commentaires="my comment",
            filter_contains__acteur_nom=None,
            filter_contains__etab_naf="test NAF",
            filter_equals__acteur_statut="ACTIF",
        )

    def test_filters_get(self, config):
        assert config.filters == [
            {
                "field": "acteur_commentaires",
                "operator": "contains",
                "value": "my comment",
            },
            {"field": "etab_naf", "operator": "contains", "value": "test NAF"},
            {"field": "acteur_statut", "operator": "equals", "value": "ACTIF"},
        ]
