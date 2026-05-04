import numpy as np
import pandas as pd
import pytest
from cluster.tasks.business_logic.cluster_acteurs_clusters import (
    cluster_acteurs_clusters,
    cluster_cols_group_fuzzy,
    score_tuples_to_clusters,
    similarity_matrix_to_tuples,
    split_clusters_by_distance,
)


def df_clusters_to_dict(df: pd.DataFrame) -> dict[str, list[str]]:
    """Helper to make clustering outputs easier to test
    by converting the clusters DataFrame into a dictionary:
    cluster_id -> list of unique identifiers
    """
    return df.groupby("cluster_id")["identifiant_unique"].apply(list).to_dict()


class TestClusterActeursClusters:

    def test_can_clusterize_exact_only(self):
        df = pd.DataFrame(
            {
                "identifiant_unique": ["id1", "id2", "id3", "id4"],
                "source_id": [1, 2, 3, 4],
                "source_code": ["s1", "s2", "s3", "s4"],
                "source_codes": [["s1"], ["s2"], ["s3"], ["s4"]],
                "ville": ["Paris", "Paris", "Laval", "Laval"],
            }
        )
        df_clusters = cluster_acteurs_clusters(
            df=df,
            cluster_fields_exact=["ville"],
            cluster_fields_fuzzy=[],
            cluster_fuzzy_threshold=0.5,
            cluster_intra_source_is_allowed=True,
        )
        assert df_clusters["cluster_id"].nunique() == 2
        clusters = [
            sorted(group["identifiant_unique"].tolist())
            for _, group in df_clusters.groupby("cluster_id")
        ]
        assert sorted(clusters) == [["id1", "id2"], ["id3", "id4"]]

    def test_can_clusterize_fuzzy_only(self):
        df = pd.DataFrame(
            {
                "identifiant_unique": ["id0", "id1", "id2", "id3"],
                "source_id": [1, 2, 3, 4],
                "source_code": ["s1", "s2", "s3", "s4"],
                "source_codes": [["s1"], ["s2"], ["s3"], ["s4"]],
                "nom": [
                    "auchan magasin",
                    "auchan boutique",
                    "carrefour depot",
                    "carrefour entrepot",
                ],
            }
        )
        df_clusters = cluster_acteurs_clusters(
            df=df,
            cluster_fields_exact=[],
            cluster_fields_fuzzy=["nom"],
            cluster_fuzzy_threshold=0.2,
            cluster_intra_source_is_allowed=True,
        )
        assert df_clusters["cluster_id"].nunique() == 2
        clusters = [
            sorted(group["identifiant_unique"].tolist())
            for _, group in df_clusters.groupby("cluster_id")
        ]
        assert sorted(clusters) == [["id0", "id1"], ["id2", "id3"]]

    def test_can_clusterize_distance_only(self):
        df = pd.DataFrame(
            {
                "identifiant_unique": ["id0", "id1", "id2", "id3"],
                "source_id": [1, 2, 3, 4],
                "source_code": ["s1", "s2", "s3", "s4"],
                "source_codes": [["s1"], ["s2"], ["s3"], ["s4"]],
                "latitude": [48.8566, 48.8567, 43.2965, 43.2966],
                "longitude": [2.3522, 2.3522, 5.3698, 5.3698],
            }
        )
        df_clusters = cluster_acteurs_clusters(
            df=df,
            cluster_fields_exact=[],
            cluster_fields_fuzzy=[],
            cluster_fuzzy_threshold=0.5,
            cluster_intra_source_is_allowed=True,
            distance_in_cluster=100,
        )
        assert df_clusters["cluster_id"].nunique() == 2
        clusters = [
            sorted(group["identifiant_unique"].tolist())
            for _, group in df_clusters.groupby("cluster_id")
        ]
        assert sorted(clusters) == [["id0", "id1"], ["id2", "id3"]]

    @pytest.fixture(scope="session")
    def df_basic(self):
        return pd.DataFrame(
            {
                "identifiant_unique": ["id1", "id2", "id3", "id4"],
                "source_id": [1, 2, 3, 4],
                "source_code": ["s1", "s2", "s3", "s4"],
                "source_codes": [["s1"], ["s2"], ["s3"], ["s4"]],
                "ville": ["Paris", "Paris", "Laval", "Laval"],
            }
        )

    def test_validation_cols_group_exact(self, df_basic):
        """Ensure the function raises when required columns are missing."""
        with pytest.raises(ValueError, match="'existe_pas' pas dans le DataFrame"):
            cluster_acteurs_clusters(df_basic, cluster_fields_exact=["existe_pas"])

    def test_validation_cols_group_fuzzy(self, df_basic):
        """Ensure the function raises when required columns are missing."""
        with pytest.raises(ValueError, match="'existe_pas' pas dans le DataFrame"):
            cluster_acteurs_clusters(df_basic, cluster_fields_fuzzy=["existe_pas"])

    # -----------------------------------------------
    # Tests for removing clusters of size 1
    # -----------------------------------------------

    @pytest.fixture(scope="session")
    def df_some_clusters_of_one(self):
        """Only the first and last rows should be grouped.

        The others are singletons (clusters of size 1) and should therefore be removed.
        """
        return pd.DataFrame(
            {
                "identifiant_unique": [
                    "id1",
                    "id2",
                    "id3",
                    "id4",
                ],
                "source_id": range(1, 5),
                "source_code": ["s1", "s2", "s3", "s4"],
                "source_codes": [["s1"], ["s2"], ["s3"], ["s4"]],
                "code_departement": ["13", "75", "53", "13"],
                "code_postal": ["13000", "75000", "53000", "13000"],
                "ville": ["Marseille", "Paris", "Laval", "Marseille"],
                "nom": ["d 1", "d 1", "d 1", "d 1"],
            }
        )

    def test_clusters_of_one_are_removed(self, df_some_clusters_of_one):
        """Check that clusters of size 1 are removed, but not clusters of size 2+."""
        df_clusters = cluster_acteurs_clusters(
            df_some_clusters_of_one,
            cluster_fields_exact=["ville"],
            cluster_fields_fuzzy=[],
            cluster_fuzzy_threshold=0.5,
            cluster_intra_source_is_allowed=True,
        )
        assert len(df_clusters) == 2
        clusters = df_clusters_to_dict(df_clusters)
        assert clusters == {
            "marseille": ["id1", "id4"],
        }

    # -----------------------------------------------
    # Tests for cluster_fields_fuzzy
    # -----------------------------------------------
    @pytest.fixture(scope="session")
    def df_cols_group_fuzzy(self):
        return pd.DataFrame(
            {
                "source_id": range(1, 8),
                "source_code": ["s1", "s1", "s1", "s1", "s1", "s1", "s1"],
                "source_codes": [["s1"] for _ in range(7)],
                "code_postal": ["10000" for _ in range(7)],
                "identifiant_unique": ["id" + str(i) for i in range(0, 7)],
                "nom": [
                    "centre commercial auchan",
                    "artiste peintre auchan",
                    "centre auchan",
                    "centre carrefour",
                    "artiste peintre",
                    "centre commercial carrefour",
                    # ignored because it is alone and we do not keep clusters of size 1
                    "je suis tout seul :(",
                ],
            }
        )

    def test_cols_group_fuzzy_single(self, df_cols_group_fuzzy):

        df_clusters = cluster_acteurs_clusters(
            df_cols_group_fuzzy,
            # code_postal is hardcoded in the clustering function
            cluster_fields_exact=["code_postal"],
            cluster_fields_fuzzy=["nom"],
            cluster_fuzzy_threshold=0.7,
            cluster_intra_source_is_allowed=True,
        )
        assert df_clusters["cluster_id"].nunique() == 3
        assert len(df_clusters) == 6
        clusters = df_clusters_to_dict(df_clusters)
        assert clusters == {
            "10000_nom_3": [
                "id0",  # "centre commercial auchan"
                "id2",  # "centre auchan"
            ],
            "10000_nom_1": [
                "id1",  # "artiste peintre auchan"
                "id4",  # "artiste peintre"
            ],
            "10000_nom_2": [
                "id3",  # "centre carrefour"
                "id5",  # "centre commercial carrefour"
            ],
        }

    def test_parent_not_discarded(self):
        """Check that parents are not discarded when children are discarded."""
        df_norm = pd.DataFrame(
            [
                {
                    "identifiant_unique": "id15",
                    "acteur_type_code": "at1",
                    "code_postal": "00004",
                    "ville": "v4",
                    "nom": "acteur c4 my s1",
                    "acteur_type_id": 3144,
                    "nombre_enfants": 0,
                    "statut": "ACTIF",
                    "source_id": 2513,
                    "source_code": "s2",
                    "source_codes": ["s2"],
                },
                {
                    "identifiant_unique": "id13",
                    "acteur_type_code": None,
                    "code_postal": "00004",
                    "ville": "v4",
                    "nom": "acteur c4 my p1 s1",
                    "acteur_type_id": 3144,
                    "nombre_enfants": 0,
                    "statut": "ACTIF",
                    "source_id": None,
                    "source_code": None,
                    "source_codes": ["s1"],
                },
                {
                    "identifiant_unique": "id14",
                    "acteur_type_code": "at1",
                    "code_postal": "00004",
                    "ville": "v4",
                    "nom": "acteur c4 my s1",
                    "acteur_type_id": 3144,
                    "nombre_enfants": 0,
                    "statut": "ACTIF",
                    "source_id": 2512,
                    "source_code": "s1",
                    "source_codes": ["s1"],
                },
            ]
        )
        df_clusters = cluster_acteurs_clusters(
            df=df_norm,
            cluster_fields_exact=["code_postal", "ville"],
            cluster_fields_fuzzy=["nom"],
            cluster_fuzzy_threshold=0.5,
            cluster_intra_source_is_allowed=True,
        )

        assert df_clusters["cluster_id"].nunique() == 1
        assert sorted(df_clusters["identifiant_unique"].tolist()) == [
            "id13",
            "id14",
            "id15",
        ]

    # -----------------------------------------------
    # Tests for splitting clusters
    # -----------------------------------------------
    @pytest.mark.django_db
    def test_cluster_intra_source(self):
        from unit_tests.qfdmo.acteur_factory import (
            ActeurTypeFactory,
            DisplayedActeurFactory,
            SourceFactory,
        )

        at1 = ActeurTypeFactory(code="at1")
        s1 = SourceFactory(code="s1")
        DisplayedActeurFactory(
            identifiant_unique="orphan1", acteur_type=at1, ville="Laval"
        )
        DisplayedActeurFactory(
            identifiant_unique="orphan2", acteur_type=at1, ville="Laval", source=s1
        )
        df = pd.DataFrame(
            {
                "identifiant_unique": ["orphan1", "orphan2"],
                "source_id": [s1.id, s1.id],
                "source_code": ["s1", "s1"],
                "source_codes": [["s1"], ["s1"]],
                "acteur_type_id": [at1.id, at1.id],
                "ville": ["Laval", "Laval"],
                "nombre_enfants": [0, 0],
                "nom": ["orphan1", "orphan2"],
            }
        )
        conf = {
            "df": df,
            "cluster_fields_exact": ["ville"],
            "cluster_fields_fuzzy": [],
            "cluster_fuzzy_threshold": 0.5,
        }
        # First testing without intra-source to show
        # we are getting no clusters
        conf["cluster_intra_source_is_allowed"] = False
        df_clusters = cluster_acteurs_clusters(**conf)
        assert len(df_clusters) == 0

        # Now testing with intra-source so get our cluster
        conf["cluster_intra_source_is_allowed"] = True
        df_clusters = cluster_acteurs_clusters(**conf)
        assert len(df_clusters) == 2


class TestClusterStrings:

    @pytest.fixture(scope="session")
    def strings(self):
        return [
            "centre commercial auchan",
            "artiste peintre auchan",
            "centre auchan",
            "centre carrefour",
            "artiste peintre",
            "centre commercial carrefour",
            "je suis tout seul :(",
        ]


class TestClusterColsGroupFuzzy:

    # Example usage
    @pytest.fixture(scope="session")
    def df_cols_group_fuzzy(self):
        data = {
            "source_id": range(0, 8),
            "col1": [
                # cluster 1
                "apple orange",
                "orphan1",  # ignored
                "orphan2",  # ignored
                "orphan3",  # ignored
                # cluster 1
                "apple orange blue",
                "apple orange blue",
                "apple orange blue green",
                "",
            ],
            "col2": [
                # A "sandwich" column with identical values to show the function
                # does not rely on a single column.
                "fruit salad",
                "fruit salad",
                "fruit salad",
                "fruit salad",
                "fruit salad",
                "fruit salad",
                "fruit salad",
                "",
            ],
            "col3": [
                # cluster 1
                "sweet",
                "sweet",
                "sour",
                "sweet",
                "sweet",
                # Cluster 2
                "bitter",
                "bitter",
                "",
            ],
        }
        return pd.DataFrame(data)

    def test_cols_group_fuzzy_multi(self, df_cols_group_fuzzy):
        clusters = cluster_cols_group_fuzzy(
            df_src=df_cols_group_fuzzy,
            columns_fuzzy=["col1", "col2", "col3"],
            threshold=0.5,
        )
        assert len(clusters) == 2
        assert clusters[0]["source_id"].tolist() == [0, 4]
        assert clusters[1]["source_id"].tolist() == [5, 6]

    def test_cols_group_fuzzy_multi_handles_empties(self):

        df = pd.DataFrame(
            {
                "col1": ["", ""],
                "col2": ["", ""],
                "col3": ["", ""],
            }
        )
        clusters = cluster_cols_group_fuzzy(
            df_src=df,
            columns_fuzzy=["col1", "col2", "col3"],
            threshold=0.5,
        )
        assert len(clusters) == 0


class TestSimilarityMatrixToTuples:

    def test_basic(self):

        matrix = np.array([[1, 0.8, 0.4], [0.8, 1, 0.9], [0.4, 0.9, 1]])
        expected = [
            (1, 2, 0.9),
            (0, 1, 0.8),
            (0, 2, 0.4),
        ]
        assert similarity_matrix_to_tuples(matrix) == expected

    def test_index_replacements(self):

        matrix = np.array([[1, 0.8, 0.4], [0.8, 1, 0.9], [0.4, 0.9, 1]])
        expected = [
            ("b", "c", 0.9),
            ("a", "b", 0.8),
            ("a", "c", 0.4),
        ]
        assert similarity_matrix_to_tuples(matrix, indexes=["a", "b", "c"]) == expected


class TestScoreTuplesToClusters:

    # Test cases
    def test_score_tuples_to_clusters(self):
        data = [
            (1, 2, 0.6),
            (2, 3, 0.6),
            (4, 5, 0.6),
            (5, 6, 0.3),  # ignored because it is below the threshold
        ]
        threshold = 0.5
        expected = [[1, 2, 3], [4, 5]]
        assert score_tuples_to_clusters(data, threshold) == expected

    def test_score_tuples_to_clusters_applies_sorting(self):
        """Check that clusters are sorted by decreasing score.

        This should hold even if the input data is not sorted.
        """
        data = [
            (5, 6, 0.3),
            (1, 2, 0.6),
            (2, 3, 0.6),
            (4, 5, 0.6),
        ]
        threshold = 0.5
        expected = [[1, 2, 3], [4, 5]]
        assert score_tuples_to_clusters(data, threshold) == expected

    def test_score_tuples_to_clusters_empty_exception(self):

        data = []
        threshold = 0.5
        with pytest.raises(ValueError, match="Liste de tuples d'entrée vide"):
            score_tuples_to_clusters(data, threshold)

    def test_score_tuples_to_clusters_no_clusters_below_threshold(self):

        data = [(1, 2, 0.3), (3, 4, 0.2)]
        threshold = 0.5
        assert score_tuples_to_clusters(data, threshold) == []

    def test_score_tuples_to_clusters_all_in_one_cluster(self):

        data = [(1, 2, 0.9), (2, 3, 0.8), (3, 4, 0.7)]
        threshold = 0.5
        expected = [[1, 2, 3, 4]]
        assert score_tuples_to_clusters(data, threshold) == expected


class TestClusterExcludeIntraSource:

    @pytest.fixture
    def df_acteurs(self):
        return pd.DataFrame(
            {
                "identifiant_unique": [
                    "a1",
                    "a2",
                    "a3",
                    "a4",
                    "a5",
                    "a6",
                    "a7",
                    "a8",
                    "a9",
                ],
                "source_codes": [
                    ["s1"],
                    ["s2"],
                    ["s1", "s3"],
                    ["s4"],
                    ["s3"],
                    ["s2"],
                    ["s3"],
                    ["s2"],
                    ["s3"],
                ],
                "nom": ["décheterie du village" for _ in range(9)],
            }
        )

    def test_cluster_split_clusterintra_source_intrasource_allowed(self, df_acteurs):
        df_clusters = cluster_acteurs_clusters(
            df_acteurs,
            cluster_fields_exact=["nom"],
            cluster_fields_fuzzy=[],
            cluster_fuzzy_threshold=0.5,
            cluster_intra_source_is_allowed=True,
        )
        assert df_clusters["cluster_id"].nunique() == 1

    def test_cluster_split_clusterintra_source_intrasource_not_allowed(
        self, df_acteurs
    ):
        df_clusters = cluster_acteurs_clusters(
            df_acteurs,
            cluster_fields_exact=["nom"],
            cluster_fields_fuzzy=[],
            cluster_fuzzy_threshold=0.5,
            cluster_intra_source_is_allowed=False,
        )
        assert df_clusters["cluster_id"].nunique() == 3


class TestSplitClustersByDistance:

    def test_returns_empty_for_cluster_of_one(self):
        df = pd.DataFrame(
            [
                {"identifiant_unique": "a", "latitude": 48.8566, "longitude": 2.3522},
            ]
        )
        assert split_clusters_by_distance(df_src=df, distance_threshold=100) == []

    def test_raises_if_missing_coordinates_columns(self):
        df = pd.DataFrame([{"identifiant_unique": "a"}, {"identifiant_unique": "b"}])
        with pytest.raises(ValueError, match="no latitude or longitude columns"):
            split_clusters_by_distance(df_src=df, distance_threshold=100)

    def test_drops_rows_with_missing_coordinates_and_returns_empty_if_not_enough_left(
        self,
    ):
        df = pd.DataFrame(
            [
                {"identifiant_unique": "a", "latitude": None, "longitude": 2.3522},
                {"identifiant_unique": "b", "latitude": 48.8566, "longitude": None},
                {"identifiant_unique": "c", "latitude": 48.8566, "longitude": 2.3522},
            ]
        )
        assert split_clusters_by_distance(df_src=df, distance_threshold=100) == []

    def test_splits_into_two_components(self):
        # (a,b) are close (~11m), (c,d) are close (~11m), but the 2 groups are far away
        df = pd.DataFrame(
            [
                {"identifiant_unique": "a", "latitude": 48.8566, "longitude": 2.3522},
                {"identifiant_unique": "b", "latitude": 48.8567, "longitude": 2.3522},
                {"identifiant_unique": "c", "latitude": 43.2965, "longitude": 5.3698},
                {"identifiant_unique": "d", "latitude": 43.2966, "longitude": 5.3698},
            ]
        )
        subclusters = split_clusters_by_distance(df_src=df, distance_threshold=100)
        assert len(subclusters) == 2

        clusters = [sorted(sc["identifiant_unique"].tolist()) for sc in subclusters]
        assert sorted(clusters) == [["a", "b"], ["c", "d"]]

    def test_chain_connectivity_creates_one_component(self):
        # a<->b close, b<->c close, but a<->c can be further away
        df = pd.DataFrame(
            [
                {"identifiant_unique": "a", "latitude": 48.8566, "longitude": 2.3522},
                {"identifiant_unique": "b", "latitude": 48.8567, "longitude": 2.3522},
                {"identifiant_unique": "c", "latitude": 48.8568, "longitude": 2.3522},
            ]
        )
        subclusters = split_clusters_by_distance(df_src=df, distance_threshold=15)
        assert len(subclusters) == 1
        assert sorted(subclusters[0]["identifiant_unique"].tolist()) == ["a", "b", "c"]
