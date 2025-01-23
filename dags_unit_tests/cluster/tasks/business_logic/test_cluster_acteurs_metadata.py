import pytest

from dags.cluster.tasks.business_logic import cluster_acteurs_metadata
from dags_unit_tests.cluster.tasks.business_logic.test_data import df_get


class TestClusterActeursMetadata:

    @pytest.fixture(scope="session")
    def df(self):
        return df_get()

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

    def test_nombre_acteurs_deja_enfant(self, meta):
        # Ceux qui on un parent_id
        assert meta["nombre_acteurs_deja_enfant"] == 2

    def test_nombre_acteurs_nouveau_enfant(self, meta):
        # 2 acteurs nouvellement clusterisés
        # = 9 - 3 déjà parents - 2 déjà clusterisés
        assert meta["nombre_acteurs_nouveau_enfant"] == 4
