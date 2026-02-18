import pytest


@pytest.mark.django_db
class TestEnrichClosedConfig:

    @pytest.fixture
    def config(self):
        from dags.enrich.config.models import EnrichActeursClosedConfig

        return EnrichActeursClosedConfig(
            dry_run=True,
            filter_contains__acteur_commentaires="my comment",
            filter_contains__acteur_nom=None,
            filter_contains__etab_naf="test NAF",
            filter_equals__acteur_statut="ACTIF",
            filter_in__acteur_type_id=[1, "2"],  # type: ignore
            filter_in__acteur_source_id=[],
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
            {"field": "acteur_type_id", "operator": "in", "value": [1, 2]},
            # acteur_source_id added because empty
        ]

    def test_ids_conversions(self, config):
        """Because we use Airflow Params dropdowns via dict values_display,
        and dict keys cannot be int, values coming back from Airflow
        will be strings to convert back to int"""
        assert config.filter_in__acteur_type_id == [1, 2]
        assert config.filter_in__acteur_source_id == []
