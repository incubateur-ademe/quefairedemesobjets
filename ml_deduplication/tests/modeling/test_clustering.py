"""Tests for the XGBoost clustering logic (ConstrainedUnionFind).

`ConstrainedUnionFind` is the core dedup-correctness structure: it merges
entities into clusters while refusing unions that violate the strict business
rules (a field that must be unique per cluster, or a field that must be equal /
compatible within a cluster).
"""

from ml_deduplication.modeling.xgboost.clustering import (
    DEFAULT_SHOULD_BE_DIFFERENT_FIELDS,
    DEFAULT_SHOULD_BE_EQUAL_FIELDS,
    ConstrainedUnionFind,
)


def _uf(
    attributes: dict,
    diff_fields: list[str] | None = None,
    eq_fields: list[str] | None = None,
) -> ConstrainedUnionFind:
    return ConstrainedUnionFind(
        entity_attributes=attributes,
        should_be_different_fields=(
            diff_fields
            if diff_fields is not None
            else list(DEFAULT_SHOULD_BE_DIFFERENT_FIELDS)
        ),
        should_be_equal_fields=(
            eq_fields if eq_fields is not None else list(DEFAULT_SHOULD_BE_EQUAL_FIELDS)
        ),
    )


class TestConstrainedUnionFind:
    def test_merges_compatible_entities(self):
        uf = _uf(
            {
                "a": {"source_id": 1, "acteur_type_id": 1},
                "b": {"source_id": 2, "acteur_type_id": 1},
            }
        )
        assert uf.union("a", "b") is True
        assert uf.find("a") == uf.find("b")

    def test_refuses_same_source_id(self):
        # same source_id -> must be different -> refuse
        uf = _uf(
            {
                "a": {"source_id": 1, "acteur_type_id": 1},
                "b": {"source_id": 1, "acteur_type_id": 1},
            }
        )
        assert uf.union("a", "b") is False
        assert uf.find("a") != uf.find("b")
        assert uf.refused_unions_count == 1

    def test_refuses_different_acteur_type(self):
        # acteur_type must be equal (and 3/4 is the only special compatibility)
        uf = _uf(
            {
                "a": {"source_id": 1, "acteur_type_id": 1},
                "b": {"source_id": 2, "acteur_type_id": 2},
            }
        )
        assert uf.union("a", "b") is False
        assert uf.find("a") != uf.find("b")

    def test_acteur_type_3_and_4_are_compatible(self):
        uf = _uf(
            {
                "a": {"source_id": 1, "acteur_type_id": 3},
                "b": {"source_id": 2, "acteur_type_id": 4},
            }
        )
        assert uf.union("a", "b") is True

    def test_null_values_do_not_create_conflicts(self):
        # one entity missing the tracked value -> no conflict on that field
        uf = _uf(
            {
                "a": {"source_id": 1, "acteur_type_id": None},
                "b": {"source_id": 2, "acteur_type_id": 1},
            }
        )
        assert uf.union("a", "b") is True

    def test_anti_transitivity_of_conflicts(self):
        # a(1) & b(2) have different sources -> merge OK. Once merged, b's
        # cluster inherits a's source (1). c(1) shares that source, so the
        # "must be different" rule refuses the b-c union: a conflict is
        # anti-transitive (a~b and b~c each fine, but not together).
        uf = _uf(
            {
                "a": {"source_id": 1, "acteur_type_id": 1},
                "b": {"source_id": 2, "acteur_type_id": 1},
                "c": {"source_id": 1, "acteur_type_id": 1},
            }
        )
        assert uf.union("a", "b") is True
        assert uf.union("b", "c") is False
        # a & c must not end up together
        assert uf.find("a") != uf.find("c")

    def test_get_clusters_groups_connected_components(self):
        uf = _uf(
            {
                "a": {"source_id": 1, "acteur_type_id": 1},
                "b": {"source_id": 2, "acteur_type_id": 1},
                "c": {"source_id": 3, "acteur_type_id": 1},
                "d": {"source_id": 4, "acteur_type_id": 1},
            }
        )
        uf.union("a", "b")
        uf.union("c", "d")
        clusters = uf.get_clusters()
        assert clusters["a"] == clusters["b"]
        assert clusters["c"] == clusters["d"]
        assert clusters["a"] != clusters["c"]

    def test_union_already_same_cluster_returns_false(self):
        uf = _uf(
            {
                "a": {"source_id": 1, "acteur_type_id": 1},
                "b": {"source_id": 2, "acteur_type_id": 1},
            }
        )
        assert uf.union("a", "b") is True
        # second union on the same pair is a no-op
        assert uf.union("a", "b") is False
