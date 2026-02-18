import numpy as np
import pandas as pd
import pytest
from cluster.tasks.business_logic.cluster_acteurs_clusters import (
    cluster_acteurs_clusters,
    cluster_cols_group_fuzzy,
    score_tuples_to_clusters,
    similarity_matrix_to_tuples,
)


def df_clusters_to_dict(df: pd.DataFrame) -> dict[str, list[str]]:
    """Utilitaire pour faciliter le test des résultats du clustering
    en convertissant la DataFrame de clusters en dictionnaire
    cluster_id -> liste des identifiants uniques
    """
    return df.groupby("cluster_id")["identifiant_unique"].apply(list).to_dict()


@pytest.mark.django_db
class TestClusterActeursClusters:

    # -----------------------------------------------
    # Tests de base
    # -----------------------------------------------

    @pytest.fixture(scope="session")
    def df_basic(self):
        return pd.DataFrame(
            {
                "identifiant_unique": [
                    "id1",
                    "id2",
                    "id3",
                    "id4-a",
                    "id4-b",
                    "id5-a",
                    "id5-b",
                ],
                "source_id": range(1, 8),
                "source_code": ["s1", "s2", "s3", "s4", "s5", "s6", "s7"],
                "source_codes": [
                    ["s1"],
                    ["s2"],
                    ["s3"],
                    ["s4"],
                    ["s5"],
                    ["s6"],
                    ["s7"],
                ],
                "code_departement": ["75", "75", "75", "75", "75", "53", "53"],
                "code_postal": [
                    "75000",
                    "75000",
                    "75000",
                    "75000",
                    "75000",
                    "53000",
                    "53000",
                ],
                "ville": [
                    "Paris",
                    "Paris",
                    "Paris",
                    "Pâris Typo",
                    "Pâris Typo",
                    "Laval",
                    "Laval",
                ],
                "nom": [
                    "decheterie 1",
                    "decheterie 2",
                    "decheterie 3",
                    "decheterie 4",
                    "decheterie 5",
                    "decheterie 6",
                    "decheterie 7",
                ],
            }
        )

    def test_cols_group_exact(self, df_basic):

        df_clusters = cluster_acteurs_clusters(
            df_basic,
            cluster_fields_exact=["ville"],
            cluster_fields_fuzzy=[],
            cluster_fuzzy_threshold=0.5,
            cluster_intra_source_is_allowed=True,
        )
        assert len(df_clusters) == len(df_basic)
        assert df_clusters["cluster_id"].nunique() == 3
        clusters = df_clusters_to_dict(df_clusters)
        assert clusters == {
            "paris": ["id1", "id2", "id3"],
            "paris-typo": ["id4-a", "id4-b"],
            "laval": ["id5-a", "id5-b"],
        }

    def test_validation_cols_group_exact(self, df_basic):
        """On s'assure que la fonction soulève une exception
        pour les colonnes manquantes dans le DataFrame"""
        with pytest.raises(ValueError, match="'existe_pas' pas dans le DataFrame"):
            cluster_acteurs_clusters(df_basic, cluster_fields_exact=["existe_pas"])

    def test_validation_cols_group_fuzzy(self, df_basic):
        """On s'assure que la fonction soulève une exception
        pour les colonnes manquantes dans le DataFrame"""
        with pytest.raises(ValueError, match="'existe_pas' pas dans le DataFrame"):
            cluster_acteurs_clusters(df_basic, cluster_fields_fuzzy=["existe_pas"])

    # -----------------------------------------------
    # Tests sur la suppression des clusters de taille 1
    # -----------------------------------------------

    @pytest.fixture(scope="session")
    def df_some_clusters_of_one(self):
        """Seules la première et la dernière ligne sont à grouper
        les autres sont des clusters de 1 et donc à supprimer"""
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
        """On vérifie qu'on supprime les clusters de taille 1 mais
        pas les autres de taille 2+"""
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
    # Tests sur cluster_fields_fuzzy
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
                    # ignoré car seul et on ne garde pas les clusters de taille 1
                    "je suis tout seul :(",
                ],
            }
        )

    def test_cols_group_fuzzy_single(self, df_cols_group_fuzzy):

        df_clusters = cluster_acteurs_clusters(
            df_cols_group_fuzzy,
            # code_postal est en dur dans la fonction de clustering
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
        """On vérifie que les parents ne sont pas ignorés
        si les enfants sont ignorés"""
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
    # Tests sur la séparation des clusters
    # -----------------------------------------------
    def test_cluster_instra_source(self):
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
                "orphan1",  # ignoré
                "orphan2",  # ignoré
                "orphan3",  # ignoré
                # cluster 1
                "apple orange blue",
                "apple orange blue",
                "apple orange blue green",
                "",
            ],
            "col2": [
                # Une colonne en sandwich avec des valeurs identiques
                # pour montrer que la fonction ne se base pas
                # sur une seule colonne
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
            (5, 6, 0.3),  # ignoré car en dessous du seuil
        ]
        threshold = 0.5
        expected = [[1, 2, 3], [4, 5]]
        assert score_tuples_to_clusters(data, threshold) == expected

    def test_score_tuples_to_clusters_applies_sorting(self):
        """On vérifie que les clusters sont triés par score décroissant
        même si la data de source n'est pas triée"""
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
