import pandas as pd
import pytest
from cluster.tasks.business_logic.misc.cluster_exclude_intra_source import (
    cluster_exclude_intra_source,
    split_cluster_intra_source,
)

ID = "identifiant_unique"


class TestClusterActeursExcludeIntraSource:
    def test_only_first_acteur_each_source_kept(self):
        # On a 3 sources et 2 acteurs par source
        # On rajoute des acteurs parents (donc sans source)
        df = pd.DataFrame(
            {
                "source_id": [None, "s1", "s2", "s3", "s3", "s2", "s1", None],
                ID: ["p1", "s1a", "s2b", "s3a", "s3b", "s2a", "s1b", "p2"],
                "cluster_id": [1, 1, 1, 1, 1, 1, 1, 1],
            }
        )
        df_kept, df_lost = cluster_exclude_intra_source(df)
        # On doit avoir conservé le premier acteur de chaque source
        # + les acteurs parents qui se retrouve à la fin due à la
        # logique fonction (concat children + parents)
        df_kept_expect = pd.DataFrame(
            {
                "source_id": ["s1", "s2", "s3", None, None],
                ID: ["s1a", "s2b", "s3a", "p1", "p2"],
                "cluster_id": [1, 1, 1, 1, 1],
            }
        )
        pd.testing.assert_frame_equal(df_kept, df_kept_expect)

        df_lost_expect = pd.DataFrame(
            {
                "source_id": [
                    "s3",
                    "s2",
                    "s1",
                ],
                ID: ["s3b", "s2a", "s1b"],
                "cluster_id": [1, 1, 1],
            }
        )
        pd.testing.assert_frame_equal(df_lost, df_lost_expect)  # type: ignore

    def test_no_changes_if_no_dup_sources(self):
        # On démontre que si il n'y a pas de doublons de sources,
        # la fonction retourne le dataframe d'origine (on voit
        # la diff avec le test précédent où ici les parents ne
        # changent pas de place)
        df = pd.DataFrame(
            {
                "source_id": [None, "s1", "s2"],
                ID: ["p1", "s1a", "s2a"],
                "cluster_id": [1, 1, 1],
            }
        )
        df_kept, df_lost = cluster_exclude_intra_source(df)
        pd.testing.assert_frame_equal(df_kept, df)
        assert df_lost is None

    def test_only_from_same_source(self):
        # La fonction en soit ne préoccupe pas
        # de la question des clusters de taille 1: elle retourne
        # un cluster avec 1 seul acteur par source, si c'est 1 tant pis,
        # on gère ça après dans la logique d'ensemble de clustering
        df = pd.DataFrame(
            {
                "source_id": ["s1", "s1", "s1"],
                ID: ["a1", "a2", "a3"],
                "cluster_id": [1, 1, 1],
            }
        )
        df_kept, df_lost = cluster_exclude_intra_source(df)
        assert df_kept[ID].tolist() == ["a1"]
        assert df_lost[ID].tolist() == ["a2", "a3"]  # type: ignore

    def test_raise_if_multi_clusters(self):
        df = pd.DataFrame(
            {
                "source_id": ["s1", "s2"],
                ID: ["a1", "a2"],
                "cluster_id": [1, 2],
            }
        )
        with pytest.raises(ValueError, match="Fonction à utiliser sur 1 seul cluster"):
            cluster_exclude_intra_source(df)


class TestClusterSplitClusterintraSource:

    @pytest.fixture
    def cluster_potential(self):
        rows = pd.DataFrame(
            {
                "id": ["a1", "a2", "a3", "a4", "a5", "a6", "a7"],
                "source_codes": [
                    ["s1"],
                    ["s2"],
                    ["s1", "s3"],
                    ["s4"],
                    ["s3"],
                    ["s2"],
                    ["s3"],
                ],
                "nom": ["décheterie du village" for _ in range(7)],
            }
        )
        return ("ctype", ["keys1", "keys2"], rows)

    def test_split_cluster_intra_source(self, cluster_potential):
        cluster_potential = split_cluster_intra_source(cluster_potential)
        assert len(cluster_potential) == 2

        df_cluster_1 = cluster_potential[0][2]
        df_cluster_2 = cluster_potential[1][2]

        assert df_cluster_1["id"].tolist() == ["a3", "a2", "a4"]
        assert df_cluster_2["id"].tolist() == ["a1", "a5", "a6"]

        # ctype
        assert cluster_potential[0][0] == "ctype"
        assert cluster_potential[1][0] == "ctype"
        # keys
        assert cluster_potential[0][1] == ["keys1", "keys2"]
        assert cluster_potential[1][1] == ["keys1", "keys2", "1"]
        # rows
        assert df_cluster_1["id"].tolist() == ["a3", "a2", "a4"]
        assert df_cluster_2["id"].tolist() == ["a1", "a5", "a6"]
