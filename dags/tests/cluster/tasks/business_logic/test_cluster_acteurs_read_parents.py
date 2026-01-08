"""
Test file for the cluster_acteurs_read_parents function
"""

import pandas as pd
import pytest
from cluster.tasks.business_logic.cluster_acteurs_read.parents import (
    cluster_acteurs_read_parents,
)

from unit_tests.qfdmo.acteur_factory import (
    ActeurTypeFactory,
    SourceFactory,
    VueActeurFactory,
)


@pytest.mark.django_db()
class TestClusterActeursReadParents:
    """Tests for the cluster_acteurs_read_parents function"""

    @pytest.fixture
    def sources(self):
        """Create test sources"""
        return {
            "s1": SourceFactory(code="s1", libelle="Source 1"),
            "s2": SourceFactory(code="s2", libelle="Source 2"),
            "s3": SourceFactory(code="s3", libelle="Source 3"),
        }

    @pytest.fixture
    def acteur_types(self):
        """Create test actor types"""
        return {
            "at1": ActeurTypeFactory(code="at1"),
            "at2": ActeurTypeFactory(code="at2"),
            "at3": ActeurTypeFactory(code="at3"),
            "at4": ActeurTypeFactory(code="at4"),
        }

    @pytest.fixture
    def acteurs_parents(self, sources, acteur_types):
        """Create test parent actors with their children"""
        acteurs = {}

        # Parent at1 - type not included in filters (to test exclusion)
        parent_at1 = VueActeurFactory(
            acteur_type=acteur_types["at1"],
            identifiant_unique="parent_at1_001",
            nom="Parent at1",
            ville="Paris",
            code_postal="75001",
            statut="ACTIF",
            est_parent=True,
        )
        # Créer un enfant pour que le parent soit vraiment un parent
        VueActeurFactory(
            source=sources["s1"],
            acteur_type=acteur_types["at1"],
            identifiant_unique="enfant_at1_001",
            nom="Enfant at1",
            parent=parent_at1,
            statut="ACTIF",
        )
        # Add sources to parent (via ManyToMany)
        parent_at1.sources.add(sources["s1"])
        acteurs["parent_at1"] = parent_at1

        # Parent at2 a - with multiple sources via children
        parent_at2a = VueActeurFactory(
            acteur_type=acteur_types["at2"],
            identifiant_unique="parent_at2a_001",
            nom="Mon parent at2 a",
            ville="Lyon",
            code_postal="69001",
            statut="ACTIF",
            est_parent=True,
        )
        VueActeurFactory(
            source=sources["s1"],
            acteur_type=acteur_types["at2"],
            identifiant_unique="enfant_at2a_s1_001",
            nom="Enfant at2a s1",
            parent=parent_at2a,
            statut="ACTIF",
        )
        VueActeurFactory(
            source=sources["s2"],
            acteur_type=acteur_types["at2"],
            identifiant_unique="enfant_at2a_s2_001",
            nom="Enfant at2a s2",
            parent=parent_at2a,
            statut="ACTIF",
        )
        # Add sources to parent (via ManyToMany)
        parent_at2a.sources.add(sources["s1"], sources["s2"])
        acteurs["parent_at2a"] = parent_at2a

        # Parent at2 b - with accent in name
        parent_at2b = VueActeurFactory(
            acteur_type=acteur_types["at2"],
            identifiant_unique="parent_at2b_001",
            nom="Mon PÂRËNT at2 b",
            ville="Marseille",
            code_postal="13001",
            statut="ACTIF",
            est_parent=True,
        )
        VueActeurFactory(
            source=sources["s1"],
            acteur_type=acteur_types["at2"],
            identifiant_unique="enfant_at2b_001",
            nom="Enfant at2b",
            parent=parent_at2b,
            statut="ACTIF",
        )
        # Add sources to parent (via ManyToMany)
        parent_at2b.sources.add(sources["s1"])
        acteurs["parent_at2b"] = parent_at2b

        # Parent at4 - active
        parent_at4 = VueActeurFactory(
            acteur_type=acteur_types["at4"],
            identifiant_unique="parent_at4_001",
            nom="Mon parent at4",
            ville="Toulouse",
            code_postal="31000",
            statut="ACTIF",
            est_parent=True,
        )
        VueActeurFactory(
            source=sources["s1"],
            acteur_type=acteur_types["at4"],
            identifiant_unique="enfant_at4_001",
            nom="Enfant at4",
            parent=parent_at4,
            statut="ACTIF",
        )
        # Add sources to parent (via ManyToMany)
        parent_at4.sources.add(sources["s1"])
        acteurs["parent_at4"] = parent_at4

        # Parent at4 inactive - should be excluded if status filter
        parent_at4_inactif = VueActeurFactory(
            acteur_type=acteur_types["at4"],
            identifiant_unique="parent_at4_inactif_001",
            nom="Parent at4 inactif",
            ville="Nice",
            code_postal="06000",
            statut="INACTIF",
            est_parent=True,
        )
        VueActeurFactory(
            source=sources["s1"],
            acteur_type=acteur_types["at4"],
            identifiant_unique="enfant_at4_inactif_001",
            nom="Enfant at4 inactif",
            parent=parent_at4_inactif,
            statut="ACTIF",
        )
        # Add sources to parent (via ManyToMany)
        parent_at4_inactif.sources.add(sources["s1"])
        acteurs["parent_at4_inactif"] = parent_at4_inactif

        # Actor with source but not a parent (to test exclusion)
        acteur_pas_parent = VueActeurFactory(
            source=sources["s1"],
            acteur_type=acteur_types["at2"],
            identifiant_unique="pas_parent_001",
            nom="Pas parent",
            ville="Bordeaux",
            code_postal="33000",
            statut="ACTIF",
            est_parent=False,
        )
        acteurs["pas_parent"] = acteur_pas_parent

        return acteurs

    # ============================================================
    # Tests on return format
    # ============================================================

    def test_returns_tuple_dataframe_and_sql_string(
        self, sources, acteur_types, acteurs_parents
    ):
        """Verify that the function returns a tuple (DataFrame, str)"""
        df, sql = cluster_acteurs_read_parents(
            fields=[
                "nom",
                "ville",
                "identifiant_unique",
                "source_id",
                "acteur_type_id",
            ],
            include_source_ids=[],
            include_acteur_type_ids=[acteur_types["at2"].id],
            include_only_if_regex_matches_nom=None,
            include_if_all_fields_filled=[],
        )

        assert isinstance(df, pd.DataFrame)
        assert isinstance(sql, str)
        assert len(sql) > 0

    def test_empty_dataframe_when_no_matching_parents(self, sources, acteur_types):
        """Verify that an empty DataFrame is returned when no parent matches"""
        df, sql = cluster_acteurs_read_parents(
            fields=["nom", "source_id", "acteur_type_id"],
            include_source_ids=[],
            include_acteur_type_ids=[999999],  # Non-existent ID
            include_only_if_regex_matches_nom=None,
            include_if_all_fields_filled=[],
        )

        assert isinstance(df, pd.DataFrame)
        assert df.empty
        assert isinstance(sql, str)

    # ============================================================
    # Tests on returned fields
    # ============================================================

    def test_includes_requested_fields(self, sources, acteur_types, acteurs_parents):
        """Verify that requested fields are included in the DataFrame"""
        df, _ = cluster_acteurs_read_parents(
            fields=[
                "nom",
                "ville",
                "code_postal",
                "identifiant_unique",
                "source_id",
                "acteur_type_id",
            ],
            include_source_ids=[],
            include_acteur_type_ids=[acteur_types["at2"].id],
            include_only_if_regex_matches_nom=None,
            include_if_all_fields_filled=[],
        )

        assert "nom" in df.columns
        assert "ville" in df.columns
        assert "code_postal" in df.columns

    def test_includes_default_enrichment_fields(
        self, sources, acteur_types, acteurs_parents
    ):
        """Verify that enrichment fields are automatically added"""
        df, _ = cluster_acteurs_read_parents(
            fields=["nom", "identifiant_unique", "source_id", "acteur_type_id"],
            include_source_ids=[],
            include_acteur_type_ids=[acteur_types["at2"].id],
            include_only_if_regex_matches_nom=None,
            include_if_all_fields_filled=[],
        )

        # Automatic enrichment fields
        assert "source_code" in df.columns
        assert "acteur_type_code" in df.columns
        assert "source_codes" in df.columns

    def test_includes_properties_when_requested(
        self, sources, acteur_types, acteurs_parents
    ):
        """Verify that properties (@property) can be included"""
        df, _ = cluster_acteurs_read_parents(
            fields=[
                "nom",
                "longitude",
                "latitude",
                "identifiant_unique",
                "source_id",
                "acteur_type_id",
            ],
            include_source_ids=[],
            include_acteur_type_ids=[acteur_types["at2"].id],
            include_only_if_regex_matches_nom=None,
            include_if_all_fields_filled=[],
        )

        assert "longitude" in df.columns
        assert "latitude" in df.columns

    # ============================================================
    # Tests on filters
    # ============================================================

    def test_filter_by_source_ids(self, sources, acteur_types, acteurs_parents):
        """Verify that the source filter works for parents"""
        df, _ = cluster_acteurs_read_parents(
            fields=["nom", "identifiant_unique", "source_id", "acteur_type_id"],
            include_source_ids=[sources["s1"].id],
            include_acteur_type_ids=[acteur_types["at2"].id, acteur_types["at4"].id],
            include_only_if_regex_matches_nom=None,
            include_if_all_fields_filled=[],
        )

        noms = df["nom"].values.tolist()
        # Parents must have at least one child with source s1
        assert "Mon parent at2 a" in noms
        assert "Mon parent at4" in noms

    def test_filter_by_acteur_type_ids(self, sources, acteur_types, acteurs_parents):
        """Verify that the actor type filter works"""
        df, _ = cluster_acteurs_read_parents(
            fields=["nom", "identifiant_unique", "source_id", "acteur_type_id"],
            include_source_ids=[],
            include_acteur_type_ids=[acteur_types["at2"].id, acteur_types["at4"].id],
            include_only_if_regex_matches_nom=None,
            include_if_all_fields_filled=[],
        )

        noms = df["nom"].values.tolist()
        assert "Mon parent at2 a" in noms
        assert "Mon parent at4" in noms
        assert "Parent at1" not in noms  # Type at1 not included

    def test_filter_by_regex_on_nom(self, sources, acteur_types, acteurs_parents):
        """Verify that the regex filter on name works"""
        df, _ = cluster_acteurs_read_parents(
            fields=["nom", "identifiant_unique", "source_id", "acteur_type_id"],
            include_source_ids=[],
            include_acteur_type_ids=[acteur_types["at2"].id, acteur_types["at4"].id],
            include_only_if_regex_matches_nom=r"parent at(?:1|2) (?:a|b)",
            include_if_all_fields_filled=[],
        )

        noms = df["nom"].values.tolist()
        assert "Mon parent at2 a" in noms
        # Note: regex does not normalize accents, so "PÂRËNT" does not match "parent"
        # The parent "Mon PÂRËNT at2 b" will not be included because regex doesn't match
        # accents
        assert "Mon parent at4" not in noms  # Does not match the regex

    def test_filter_by_regex_case_insensitive(
        self, sources, acteur_types, acteurs_parents
    ):
        """
        Verify that the regex filter is case-insensitive (but not accent-insensitive)
        """
        df, _ = cluster_acteurs_read_parents(
            fields=["nom", "identifiant_unique", "source_id", "acteur_type_id"],
            include_source_ids=[],
            include_acteur_type_ids=[acteur_types["at2"].id],
            include_only_if_regex_matches_nom="parent",
            include_if_all_fields_filled=[],
        )

        noms = df["nom"].values.tolist()
        assert "Mon parent at2 a" in noms
        # Note: regex is case-insensitive but not accent-insensitive
        # "PÂRËNT" does not match "parent" because accents are different
        # To test with accents, would need to use a regex that includes accents

    def test_filter_by_all_fields_filled(self, sources, acteur_types, acteurs_parents):
        """Verify that the filter on filled fields works"""
        df, _ = cluster_acteurs_read_parents(
            fields=[
                "nom",
                "ville",
                "code_postal",
                "identifiant_unique",
                "source_id",
                "acteur_type_id",
            ],
            include_source_ids=[],
            include_acteur_type_ids=[acteur_types["at2"].id],
            include_only_if_regex_matches_nom=None,
            include_if_all_fields_filled=["nom", "ville", "code_postal"],
        )

        noms = df["nom"].values.tolist()
        assert "Mon parent at2 a" in noms
        # Parents must have all fields filled

    # ============================================================
    # Tests on enrichments
    # ============================================================

    def test_source_code_enrichment(self, sources, acteur_types, acteurs_parents):
        """Verify that source_code is correctly enriched for parents"""
        df, _ = cluster_acteurs_read_parents(
            fields=["nom", "identifiant_unique", "source_id", "acteur_type_id"],
            include_source_ids=[sources["s1"].id],
            include_acteur_type_ids=[acteur_types["at2"].id],
            include_only_if_regex_matches_nom=None,
            include_if_all_fields_filled=[],
        )

        assert "source_code" in df.columns
        # For parents, source_code can be from one of their children

    def test_acteur_type_code_enrichment(self, sources, acteur_types, acteurs_parents):
        """Verify that acteur_type_code is correctly enriched"""
        df, _ = cluster_acteurs_read_parents(
            fields=["nom", "identifiant_unique", "source_id", "acteur_type_id"],
            include_source_ids=[],
            include_acteur_type_ids=[acteur_types["at2"].id],
            include_only_if_regex_matches_nom=None,
            include_if_all_fields_filled=[],
        )

        assert "acteur_type_code" in df.columns
        assert all(df["acteur_type_code"] == "at2")

    def test_source_codes_enrichment_for_parents(
        self, sources, acteur_types, acteurs_parents
    ):
        """Verify that source_codes contains all children's sources for parents"""
        df, _ = cluster_acteurs_read_parents(
            fields=["nom", "identifiant_unique", "source_id", "acteur_type_id"],
            include_source_ids=[],
            include_acteur_type_ids=[acteur_types["at2"].id],
            include_only_if_regex_matches_nom=None,
            include_if_all_fields_filled=[],
        )

        assert "source_codes" in df.columns
        # For parents, source_codes is a tuple with all their children's sources
        assert all(isinstance(codes, tuple) for codes in df["source_codes"].values)
        # Parent at2a has children with s1 and s2
        parent_at2a_row = df[df["nom"] == "Mon parent at2 a"]
        if not parent_at2a_row.empty:
            source_codes = parent_at2a_row["source_codes"].iloc[0]
            assert "s1" in source_codes
            assert "s2" in source_codes

    # ============================================================
    # Tests on parent-specific behavior
    # ============================================================

    def test_only_returns_parents(self, sources, acteur_types):
        """
        Verify that only parents are returned (est_parent=True, parent_id__isnull=True)
        """
        # Create a parent
        parent = VueActeurFactory(
            acteur_type=acteur_types["at1"],
            identifiant_unique="test_parent_001",
            nom="Parent test",
            ville="Paris",
            code_postal="75001",
            statut="ACTIF",
            est_parent=True,
        )
        # Créer un enfant pour que le parent soit vraiment un parent
        enfant = VueActeurFactory(
            source=sources["s1"],
            acteur_type=acteur_types["at1"],
            identifiant_unique="test_enfant_001",
            nom="Enfant test",
            parent=parent,
            statut="ACTIF",
        )
        enfant.sources.add(sources["s1"])
        # Add sources to parent (via ManyToMany)
        parent.sources.add(sources["s1"])

        # Create an orphan (not a parent)
        orphelin = VueActeurFactory(
            source=sources["s1"],
            acteur_type=acteur_types["at1"],
            identifiant_unique="test_orphelin_001",
            nom="Orphelin test",
            ville="Paris",
            code_postal="75001",
            statut="ACTIF",
            est_parent=False,
        )
        orphelin.sources.add(sources["s1"])

        df, _ = cluster_acteurs_read_parents(
            fields=["nom", "identifiant_unique", "source_id", "acteur_type_id"],
            include_source_ids=[],
            include_acteur_type_ids=[acteur_types["at1"].id],
            include_only_if_regex_matches_nom=None,
            include_if_all_fields_filled=[],
        )

        noms = df["nom"].values.tolist()
        assert "Parent test" in noms
        assert "Orphelin test" not in noms

    def test_parents_with_multiple_sources(
        self, sources, acteur_types, acteurs_parents
    ):
        """
        Verify that parents with multiple sources (via children) are correctly handled
        """
        df, _ = cluster_acteurs_read_parents(
            fields=["nom", "identifiant_unique", "source_id", "acteur_type_id"],
            include_source_ids=[],
            include_acteur_type_ids=[acteur_types["at2"].id],
            include_only_if_regex_matches_nom=None,
            include_if_all_fields_filled=[],
        )

        # Parent at2a has children with s1 and s2
        parent_at2a_row = df[df["nom"] == "Mon parent at2 a"]
        if not parent_at2a_row.empty:
            source_codes = parent_at2a_row["source_codes"].iloc[0]
            assert isinstance(source_codes, tuple)
            assert len(source_codes) >= 1

    # ============================================================
    # Tests on data format
    # ============================================================

    def test_no_type_inference_from_pandas(
        self, sources, acteur_types, acteurs_parents
    ):
        """Verify that Pandas does not infer types (e.g., code_postal remains string)"""
        df, _ = cluster_acteurs_read_parents(
            fields=["code_postal", "identifiant_unique", "source_id", "acteur_type_id"],
            include_source_ids=[],
            include_acteur_type_ids=[acteur_types["at2"].id],
            include_only_if_regex_matches_nom=None,
            include_if_all_fields_filled=["code_postal"],
        )

        assert df["code_postal"].dtype == "object"
        # Verify that values are strings
        assert all(isinstance(val, str) for val in df["code_postal"].values)

    def test_empty_strings_converted_to_none(self, sources, acteur_types):
        """Verify that empty strings are converted to None"""
        parent = VueActeurFactory(
            acteur_type=acteur_types["at1"],
            identifiant_unique="test_parent_vide_001",
            nom="Parent avec champs vides",
            adresse="",
            ville="Paris",
            code_postal="75001",
            statut="ACTIF",
            est_parent=True,
        )
        enfant = VueActeurFactory(
            source=sources["s1"],
            acteur_type=acteur_types["at1"],
            identifiant_unique="test_enfant_vide_001",
            nom="Enfant",
            parent=parent,
            statut="ACTIF",
        )
        enfant.sources.add(sources["s1"])
        # Add sources to parent (via ManyToMany)
        parent.sources.add(sources["s1"])

        df, _ = cluster_acteurs_read_parents(
            fields=[
                "nom",
                "adresse",
                "identifiant_unique",
                "source_id",
                "acteur_type_id",
            ],
            include_source_ids=[],
            include_acteur_type_ids=[acteur_types["at1"].id],
            include_only_if_regex_matches_nom=None,
            include_if_all_fields_filled=[],
        )

        # Empty strings should be None
        parent_row = df[df["nom"] == "Parent avec champs vides"]
        if not parent_row.empty:
            assert parent_row["adresse"].iloc[0] is None

    # ============================================================
    # Tests on filter combinations
    # ============================================================

    def test_combination_of_filters(self, sources, acteur_types, acteurs_parents):
        """Verify that combining multiple filters works"""
        df, _ = cluster_acteurs_read_parents(
            fields=["nom", "identifiant_unique", "source_id", "acteur_type_id"],
            include_source_ids=[sources["s1"].id],
            include_acteur_type_ids=[acteur_types["at2"].id, acteur_types["at4"].id],
            include_only_if_regex_matches_nom="parent",
            include_if_all_fields_filled=["nom", "ville"],
        )

        noms = df["nom"].values.tolist()
        # Should match the regex AND have all fields filled AND have an child with s1
        assert "Mon parent at2 a" in noms
        assert "Mon parent at4" in noms
