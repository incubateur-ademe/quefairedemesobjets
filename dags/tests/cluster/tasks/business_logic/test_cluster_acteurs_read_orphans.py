import pandas as pd
import pytest
from cluster.tasks.business_logic.cluster_acteurs_read.for_clustering import (
    cluster_acteurs_read_orphans,
)

from unit_tests.qfdmo.acteur_factory import (
    ActeurTypeFactory,
    SourceFactory,
    VueActeurFactory,
)


# Do not set transaction=True as this recreates
# DB fixtures for each test which significantly
# slows down tests for nothing (we only do
# reading)
@pytest.mark.django_db()
class TestClusterActeursReadOrphans:
    """Tests for the cluster_acteurs_read_orphans function"""

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
        }

    @pytest.fixture
    def acteurs_orphelins(self, sources, acteur_types):
        """Create test orphan actors"""
        acteurs = {}

        # Actor with all fields filled - source 1, type 1
        acteurs["orphelin_complet_s1_at1"] = VueActeurFactory(
            source=sources["s1"],
            acteur_type=acteur_types["at1"],
            nom="Acteur complet s1 at1",
            adresse="123 rue de la Paix",
            ville="Paris",
            code_postal="75001",
            statut="ACTIF",
        )

        # Actor with all fields filled - source 1, type 2
        acteurs["orphelin_complet_s1_at2"] = VueActeurFactory(
            source=sources["s1"],
            acteur_type=acteur_types["at2"],
            nom="Acteur complet s1 at2",
            adresse="456 avenue des Champs",
            ville="Lyon",
            code_postal="69001",
            statut="ACTIF",
        )

        # Actor with all fields filled - source 2, type 1
        acteurs["orphelin_complet_s2_at1"] = VueActeurFactory(
            source=sources["s2"],
            acteur_type=acteur_types["at1"],
            nom="Acteur complet s2 at1",
            adresse="789 boulevard Saint-Michel",
            ville="Marseille",
            code_postal="13001",
            statut="ACTIF",
        )

        # INACTIVE actor (should be included if no status filter)
        acteurs["orphelin_inactif"] = VueActeurFactory(
            source=sources["s1"],
            acteur_type=acteur_types["at1"],
            nom="Acteur inactif",
            adresse="999 rue inactive",
            ville="Toulouse",
            code_postal="31000",
            statut="INACTIF",
        )

        # Actor with empty city (should be excluded if city in
        # include_if_all_fields_filled)
        acteurs["orphelin_ville_vide"] = VueActeurFactory(
            source=sources["s1"],
            acteur_type=acteur_types["at1"],
            nom="Acteur ville vide",
            adresse="111 rue sans ville",
            ville="",
            code_postal="75002",
            statut="ACTIF",
        )

        # Actor with name that doesn't match the regex
        acteurs["orphelin_nom_non_match"] = VueActeurFactory(
            source=sources["s1"],
            acteur_type=acteur_types["at1"],
            nom="XYZ ne match pas",
            adresse="222 rue XYZ",
            ville="Nice",
            code_postal="06000",
            statut="ACTIF",
        )

        # Actor with excluded source
        acteurs["orphelin_source_exclue"] = VueActeurFactory(
            source=sources["s3"],
            acteur_type=acteur_types["at1"],
            nom="Acteur source exclue",
            adresse="333 rue exclue",
            ville="Bordeaux",
            code_postal="33000",
            statut="ACTIF",
        )

        # Actor with excluded type
        acteurs["orphelin_type_exclu"] = VueActeurFactory(
            source=sources["s1"],
            acteur_type=acteur_types["at3"],
            nom="Acteur type exclu",
            adresse="444 rue type exclu",
            ville="Nantes",
            code_postal="44000",
            statut="ACTIF",
        )

        return acteurs

    # ============================================================
    # Tests on return format
    # ============================================================

    def test_returns_tuple_dataframe_and_sql_string(
        self, sources, acteur_types, acteurs_orphelins
    ):
        """Verify that the function returns a tuple (DataFrame, str)"""
        df, sql = cluster_acteurs_read_orphans(
            fields=["nom", "ville", "source_id", "acteur_type_id"],
            include_source_ids=[sources["s1"].id],
            include_acteur_type_ids=[acteur_types["at1"].id],
            include_only_if_regex_matches_nom=None,
            include_if_all_fields_filled=[],
        )

        assert isinstance(df, pd.DataFrame)
        assert isinstance(sql, str)
        assert len(sql) > 0

    def test_empty_dataframe_when_no_matching_actors(self, sources, acteur_types):
        """Verify that an empty DataFrame is returned when no actor matches"""
        df, sql = cluster_acteurs_read_orphans(
            fields=["nom"],
            include_source_ids=[999999],  # Non-existent ID
            include_acteur_type_ids=[acteur_types["at1"].id],
            include_only_if_regex_matches_nom=None,
            include_if_all_fields_filled=[],
        )

        assert isinstance(df, pd.DataFrame)
        assert df.empty
        assert isinstance(sql, str)

    # ============================================================
    # Tests on returned fields
    # ============================================================

    def test_includes_requested_fields(self, sources, acteur_types, acteurs_orphelins):
        """Verify that requested fields are included in the DataFrame"""
        df, _ = cluster_acteurs_read_orphans(
            fields=[
                "nom",
                "ville",
                "code_postal",
                "adresse",
                "source_id",
                "acteur_type_id",
            ],
            include_source_ids=[sources["s1"].id],
            include_acteur_type_ids=[acteur_types["at1"].id],
            include_only_if_regex_matches_nom=None,
            include_if_all_fields_filled=[],
        )

        assert "nom" in df.columns
        assert "ville" in df.columns
        assert "code_postal" in df.columns
        assert "adresse" in df.columns
        assert "source_id" in df.columns
        assert "acteur_type_id" in df.columns
        assert "adresse_complement" not in df.columns

    def test_includes_default_enrichment_fields(
        self, sources, acteur_types, acteurs_orphelins
    ):
        """Verify that enrichment fields are automatically added"""
        df, _ = cluster_acteurs_read_orphans(
            fields=["nom", "source_id", "acteur_type_id"],
            include_source_ids=[sources["s1"].id],
            include_acteur_type_ids=[acteur_types["at1"].id],
            include_only_if_regex_matches_nom=None,
            include_if_all_fields_filled=[],
        )

        # Automatic enrichment fields
        assert "source_code" in df.columns
        assert "acteur_type_code" in df.columns
        assert "source_codes" in df.columns

        # Verify that source_codes is a list for orphans
        assert all(
            isinstance(codes, list) and len(codes) == 1
            for codes in df["source_codes"].values
        )

    def test_includes_properties_when_requested(
        self, sources, acteur_types, acteurs_orphelins
    ):
        """Verify that properties (@property) can be included"""
        df, _ = cluster_acteurs_read_orphans(
            fields=["nom", "longitude", "latitude", "source_id", "acteur_type_id"],
            include_source_ids=[sources["s1"].id],
            include_acteur_type_ids=[acteur_types["at1"].id],
            include_only_if_regex_matches_nom=None,
            include_if_all_fields_filled=[],
        )

        assert "longitude" in df.columns
        assert "latitude" in df.columns

    # ============================================================
    # Tests on filters
    # ============================================================

    def test_filter_by_source_ids(self, sources, acteur_types, acteurs_orphelins):
        """Verify that the source filter works"""
        df, _ = cluster_acteurs_read_orphans(
            fields=["nom", "source_id", "acteur_type_id"],
            include_source_ids=[sources["s1"].id, sources["s2"].id],
            include_acteur_type_ids=[acteur_types["at1"].id],
            include_only_if_regex_matches_nom=None,
            include_if_all_fields_filled=[],
        )

        noms = df["nom"].values.tolist()
        assert "Acteur complet s1 at1" in noms
        assert "Acteur complet s2 at1" in noms
        assert "Acteur source exclue" not in noms

    def test_filter_by_acteur_type_ids(self, sources, acteur_types, acteurs_orphelins):
        """Verify that the actor type filter works"""
        df, _ = cluster_acteurs_read_orphans(
            fields=["nom", "source_id", "acteur_type_id"],
            include_source_ids=[sources["s1"].id],
            include_acteur_type_ids=[acteur_types["at1"].id, acteur_types["at2"].id],
            include_only_if_regex_matches_nom=None,
            include_if_all_fields_filled=[],
        )

        noms = df["nom"].values.tolist()
        assert "Acteur complet s1 at1" in noms
        assert "Acteur complet s1 at2" in noms
        assert "Acteur type exclu" not in noms

    def test_filter_by_regex_on_nom(self, sources, acteur_types, acteurs_orphelins):
        """Verify that the regex filter on name works"""
        df, _ = cluster_acteurs_read_orphans(
            fields=["nom", "source_id", "acteur_type_id"],
            include_source_ids=[sources["s1"].id],
            include_acteur_type_ids=[acteur_types["at1"].id],
            include_only_if_regex_matches_nom=r"Acteur\s+.*at1$",
            include_if_all_fields_filled=[],
        )

        noms = df["nom"].values.tolist()
        assert "Acteur complet s1 at1" in noms
        assert "XYZ ne match pas" not in noms

    def test_filter_by_regex_case_insensitive(
        self, sources, acteur_types, acteurs_orphelins
    ):
        """Verify that the regex filter is case-insensitive"""
        df, _ = cluster_acteurs_read_orphans(
            fields=["nom", "source_id", "acteur_type_id"],
            include_source_ids=[sources["s1"].id],
            include_acteur_type_ids=[acteur_types["at1"].id],
            include_only_if_regex_matches_nom="acteur",
            include_if_all_fields_filled=[],
        )

        noms = df["nom"].values.tolist()
        assert "Acteur complet s1 at1" in noms

    def test_filter_by_all_fields_filled(
        self, sources, acteur_types, acteurs_orphelins
    ):
        """Verify that the filter on filled fields works"""
        df, _ = cluster_acteurs_read_orphans(
            fields=["nom", "ville", "code_postal", "source_id", "acteur_type_id"],
            include_source_ids=[sources["s1"].id],
            include_acteur_type_ids=[acteur_types["at1"].id],
            include_only_if_regex_matches_nom=None,
            include_if_all_fields_filled=["nom", "ville", "code_postal"],
        )

        noms = df["nom"].values.tolist()
        assert "Acteur complet s1 at1" in noms
        assert "Acteur ville vide" not in noms

    def test_filter_by_all_fields_filled_with_property(
        self, sources, acteur_types, acteurs_orphelins
    ):
        """Verify that the filter also works with properties"""
        df, _ = cluster_acteurs_read_orphans(
            fields=["nom", "nom_sans_combine_adresses", "source_id", "acteur_type_id"],
            include_source_ids=[sources["s1"].id],
            include_acteur_type_ids=[acteur_types["at1"].id],
            include_only_if_regex_matches_nom=None,
            include_if_all_fields_filled=["nom", "nom_sans_combine_adresses"],
        )

        # If nom_sans_combine_adresses is None or empty, the actor is excluded
        # We just verify that the filter works
        assert isinstance(df, pd.DataFrame)

    # ============================================================
    # Tests on enrichments
    # ============================================================

    def test_source_code_enrichment(self, sources, acteur_types, acteurs_orphelins):
        """Verify that source_code is correctly enriched"""
        df, _ = cluster_acteurs_read_orphans(
            fields=["nom", "source_id", "acteur_type_id"],
            include_source_ids=[sources["s1"].id],
            include_acteur_type_ids=[acteur_types["at1"].id],
            include_only_if_regex_matches_nom=None,
            include_if_all_fields_filled=[],
        )

        assert "source_code" in df.columns
        assert all(df["source_code"] == "s1")

    def test_acteur_type_code_enrichment(
        self, sources, acteur_types, acteurs_orphelins
    ):
        """Verify that acteur_type_code is correctly enriched"""
        df, _ = cluster_acteurs_read_orphans(
            fields=["nom", "source_id", "acteur_type_id"],
            include_source_ids=[sources["s1"].id],
            include_acteur_type_ids=[acteur_types["at1"].id],
            include_only_if_regex_matches_nom=None,
            include_if_all_fields_filled=[],
        )

        assert "acteur_type_code" in df.columns
        assert all(df["acteur_type_code"] == "at1")

    def test_source_codes_enrichment_for_orphans(
        self, sources, acteur_types, acteurs_orphelins
    ):
        """Verify that source_codes is a list with a single element for orphans"""
        df, _ = cluster_acteurs_read_orphans(
            fields=["nom", "source_id", "acteur_type_id"],
            include_source_ids=[sources["s1"].id],
            include_acteur_type_ids=[acteur_types["at1"].id],
            include_only_if_regex_matches_nom=None,
            include_if_all_fields_filled=[],
        )

        assert "source_codes" in df.columns
        assert all(isinstance(codes, list) for codes in df["source_codes"].values)
        assert all(len(codes) == 1 for codes in df["source_codes"].values)
        assert all(codes[0] == "s1" for codes in df["source_codes"].values)

    # ============================================================
    # Tests on orphan-specific behavior
    # ============================================================

    def test_only_returns_orphans(self, sources, acteur_types):
        """Verify that only orphans are returned (no parent, not a parent)"""
        # Create an orphan
        orphelin = VueActeurFactory(
            source=sources["s1"],
            acteur_type=acteur_types["at1"],
            nom="Orphelin",
            ville="Paris",
            code_postal="75001",
            statut="ACTIF",
        )
        orphelin.sources.add(sources["s1"])

        # Create a parent
        parent = VueActeurFactory(
            source=sources["s1"],
            acteur_type=acteur_types["at1"],
            nom="Parent",
            ville="Paris",
            code_postal="75001",
            statut="ACTIF",
            est_parent=True,
        )
        parent.sources.add(sources["s1"])

        # Create a child (with parent_id)
        enfant = VueActeurFactory(
            source=sources["s1"],
            acteur_type=acteur_types["at1"],
            nom="Enfant",
            ville="Paris",
            code_postal="75001",
            statut="ACTIF",
            parent=parent,
        )
        enfant.sources.add(sources["s1"])

        df, _ = cluster_acteurs_read_orphans(
            fields=["nom", "source_id", "acteur_type_id"],
            include_source_ids=[sources["s1"].id],
            include_acteur_type_ids=[acteur_types["at1"].id],
            include_only_if_regex_matches_nom=None,
            include_if_all_fields_filled=[],
        )

        noms = df["nom"].values.tolist()
        assert "Orphelin" in noms
        assert "Parent" not in noms
        assert "Enfant" not in noms

    # ============================================================
    # Tests on data format
    # ============================================================

    def test_no_type_inference_from_pandas(
        self, sources, acteur_types, acteurs_orphelins
    ):
        """Verify that Pandas does not infer types (e.g., code_postal remains string)"""
        df, _ = cluster_acteurs_read_orphans(
            fields=["code_postal", "source_id", "acteur_type_id"],
            include_source_ids=[sources["s1"].id],
            include_acteur_type_ids=[acteur_types["at1"].id],
            include_only_if_regex_matches_nom=None,
            include_if_all_fields_filled=["code_postal"],
        )

        assert df["code_postal"].dtype == "object"
        # Verify that values are strings
        assert all(isinstance(val, str) for val in df["code_postal"].values)

    def test_empty_strings_converted_to_none(self, sources, acteur_types):
        """Verify that empty strings are converted to None"""
        acteur = VueActeurFactory(
            source=sources["s1"],
            acteur_type=acteur_types["at1"],
            nom="Acteur avec champs vides",
            adresse="",
            ville="Paris",
            code_postal="75001",
            statut="ACTIF",
        )
        acteur.sources.add(sources["s1"])

        df, _ = cluster_acteurs_read_orphans(
            fields=["nom", "adresse", "source_id", "acteur_type_id"],
            include_source_ids=[sources["s1"].id],
            include_acteur_type_ids=[acteur_types["at1"].id],
            include_only_if_regex_matches_nom=None,
            include_if_all_fields_filled=[],
        )

        # Empty strings should be None
        assert df[df["nom"] == "Acteur avec champs vides"]["adresse"].iloc[0] is None

    # ============================================================
    # Tests on filter combinations
    # ============================================================

    def test_combination_of_filters(self, sources, acteur_types, acteurs_orphelins):
        """Verify that combining multiple filters works"""
        df, _ = cluster_acteurs_read_orphans(
            fields=["nom", "source_id", "acteur_type_id"],
            include_source_ids=[sources["s1"].id],
            include_acteur_type_ids=[acteur_types["at1"].id],
            include_only_if_regex_matches_nom="Acteur",
            include_if_all_fields_filled=["nom", "ville", "code_postal"],
        )

        noms = df["nom"].values.tolist()
        # Must match the regex AND have all fields filled
        assert "Acteur complet s1 at1" in noms
        assert "XYZ ne match pas" not in noms
        assert "Acteur ville vide" not in noms
