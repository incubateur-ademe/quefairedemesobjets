import pytest
from django.contrib.gis.geos import Point
from unit_tests.qfdmo.acteur_factory import (
    ActeurTypeFactory,
    SourceFactory,
    VueActeurFactory,
)
from utils.django import django_setup_full

from dags.cluster.tasks.business_logic.cluster_acteurs_read.for_clustering import (
    _cluster_acteurs_read_base,
)

django_setup_full()


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------
@pytest.fixture
def acteur_type():
    return ActeurTypeFactory(code="t1")


@pytest.fixture
def sources():
    return [SourceFactory() for _ in range(2)]


@pytest.fixture
def vue_acteurs_orphans(acteur_type, sources):
    """Acteurs orphelins (parent=None, est_parent=False) de 2 sources différentes."""
    return [
        VueActeurFactory(
            identifiant_unique="a1",
            nom="acteur source 1",
            siret="11111111111111",
            source=sources[0],
            location=Point(0, 0),
            acteur_type=acteur_type,
            parent=None,
            est_parent=False,
        ),
        VueActeurFactory(
            identifiant_unique="a2",
            nom="acteur source 2",
            siret="22222222222222",
            source=sources[1],
            location=Point(1, 1),
            acteur_type=acteur_type,
            parent=None,
            est_parent=False,
        ),
    ]


# ---------------------------------------------------------------------------
# Tests : _cluster_acteurs_read_base - exclude_source_ids
# ---------------------------------------------------------------------------
class TestClusterActeursReadBaseExcludeSourceIds:
    """Tests for the ``exclude_source_ids`` parameter on
    ``_cluster_acteurs_read_base``."""

    @pytest.mark.django_db
    def test_exclude_source_ids_filters_orphans(self, vue_acteurs_orphans, sources):
        """When ``exclude_source_ids`` is provided, actors from those
        source IDs must be filtered out from the result."""
        # 'source_id' and 'acteur_type_id' are required: the base function
        # accesses them to build 'source_code' and 'auteur_type_code'.
        fields = [
            "nom",
            "siret",
            "identifiant_unique",
            "source_id",
            "acteur_type_id",
        ]

        # No exclusion → both actors are returned.
        df_all, _ = _cluster_acteurs_read_base(
            fields=fields,
            include_source_ids=[],
            exclude_source_ids=[],
            include_acteur_type_ids=[],
            include_only_if_regex_matches_nom=None,
            include_if_all_fields_filled=[],
            est_parent=False,
        )
        assert set(df_all["identifiant_unique"]) == {"a1", "a2"}

        # Exclude source 0 → only a2 (from source 1) should remain.
        df_excluded, _ = _cluster_acteurs_read_base(
            fields=fields,
            include_source_ids=[],
            exclude_source_ids=[sources[0].id],
            include_acteur_type_ids=[],
            include_only_if_regex_matches_nom=None,
            include_if_all_fields_filled=[],
            est_parent=False,
        )
        assert set(df_excluded["identifiant_unique"]) == {"a2"}

    @pytest.mark.django_db
    def test_exclude_source_ids_with_include_source_ids(self, vue_acteurs_orphans):
        """``exclude_source_ids`` works in tandem with ``include_source_ids``:
        actors from an included but also excluded source are filtered out."""
        fields = [
            "nom",
            "siret",
            "identifiant_unique",
            "source_id",
            "acteur_type_id",
        ]

        # Include source 0, exclude nothing → only a1.
        df_include_only, _ = _cluster_acteurs_read_base(
            fields=fields,
            include_source_ids=[vue_acteurs_orphans[0].source_id],
            exclude_source_ids=[],
            include_acteur_type_ids=[],
            include_only_if_regex_matches_nom=None,
            include_if_all_fields_filled=[],
            est_parent=False,
        )
        assert set(df_include_only["identifiant_unique"]) == {"a1"}

        # Include source 0, but exclude it → empty result.
        df_both, _ = _cluster_acteurs_read_base(
            fields=fields,
            include_source_ids=[vue_acteurs_orphans[0].source_id],
            exclude_source_ids=[vue_acteurs_orphans[0].source_id],
            include_acteur_type_ids=[],
            include_only_if_regex_matches_nom=None,
            include_if_all_fields_filled=[],
            est_parent=False,
        )
        assert df_both.empty
