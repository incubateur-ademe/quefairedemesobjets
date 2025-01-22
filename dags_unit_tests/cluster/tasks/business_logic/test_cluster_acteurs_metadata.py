import pandas as pd
import pytest

from dags.cluster.tasks.business_logic.cluster_acteurs_metadata import (
    cluster_acteurs_metadata,
)


class TestClusterActeursMetadata:

    @pytest.fixture(scope="session")
    def df(self):
        """
        Cas de figures à couvrir:
        Cluster 1 = 0 parent existant + 2 enfants
        Cluster 2 = 1 parent existant + 2 enfants, dont 1 déjà rattaché
        Cluster 3 = 2 parents existants + 2 enfants, dont 1 déjà rattaché

        """
        return pd.DataFrame(
            {
                "cluster_id": [
                    # Cluster 1
                    "c1_0parent_2act",
                    "c1_0parent_2act",
                    # Cluster 2
                    "c2_1parent_3act",
                    "c2_1parent_3act",
                    "c2_1parent_3act",
                    # Cluster 3
                    "c3_2parent_4act",
                    "c3_2parent_4act",
                    "c3_2parent_4act",
                    "c3_2parent_4act",
                ],
                "identifiant_unique": [
                    # Cluster 1
                    "A",
                    "B",
                    # Cluster 2
                    "C",
                    "D",
                    "E",
                    # Cluster 3
                    "F",
                    "G",
                    "H",
                    "I",
                ],
                "parent_id": [
                    # Cluster 1
                    None,
                    None,
                    # Cluster 2
                    "C",
                    None,
                    None,
                    # Cluster 3
                    "F",
                    None,
                    None,
                    None,
                ],
                "is_parent_current": [
                    # Cluster 1
                    False,
                    False,
                    # Cluster 2
                    False,
                    True,
                    False,
                    # Cluster 3
                    False,
                    True,
                    True,
                    False,
                ],
                "is_parent_to_delete": [
                    # Cluster 1
                    False,
                    False,
                    # Cluster 2
                    False,
                    False,
                    False,
                    # Cluster 3
                    False,
                    True,
                    False,
                    False,
                ],
                "is_parent_to_keep": [
                    # Cluster 1
                    True,
                    False,
                    # Cluster 2
                    False,
                    True,
                    False,
                    # Cluster 3
                    False,
                    False,
                    True,
                    False,
                ],
            }
        )

    @pytest.fixture(scope="session")
    def meta(self, df):
        return cluster_acteurs_metadata(df)

    def test_nombre_clusters(self, meta):
        # Clusters 1, 2 et 3
        assert meta["nombre_clusters"] == 3

    def test_nombre_clusters_existants(self, meta):
        # Tous les clusters sont existants sauf cluster 1
        assert meta["nombre_clusters_existants"] == 2

    def test_nombre_clusters_nouveaux(self, meta):
        # Cluster 1 est nouveau
        assert meta["nombre_clusters_nouveaux"] == 1

    def test_nombre_acteurs(self, meta):
        # 9 acteurs
        assert meta["nombre_acteurs"] == 9

    def test_nombre_acteurs_deja_parent(self, meta):
        # 3 acteurs déjà parent
        assert meta["nombre_acteurs_deja_parent"] == 3

    def test_nombre_acteurs_deja_clusterises(self, meta):
        # Ceux qui on un parent_id
        assert meta["nombre_acteurs_deja_clusterises"] == 2

    def test_nombre_acteurs_nouvellement_clusterises(self, meta):
        # 2 acteurs nouvellement clusterisés
        # = 9 - 3 déjà parents - 2 déjà clusterisés
        assert meta["nombre_acteurs_nouvellement_clusterises"] == 4
