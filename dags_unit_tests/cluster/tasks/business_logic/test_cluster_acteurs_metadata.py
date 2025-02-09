import pandas as pd
import pytest

from dags.cluster.tasks.business_logic import cluster_acteurs_metadata
from dags.cluster.tasks.business_logic.cluster_acteurs_metadata import (
    COUNT_ACTEURS,
    COUNT_ACTEURS_CURRENT,
    COUNT_ACTEURS_NEW,
    COUNT_CLUSTERS,
    COUNT_CLUSTERS_CURRENT,
    COUNT_CLUSTERS_NET,
)


class TestClusterActeursMetadata:

    @pytest.fixture(scope="session")
    def df(self):
        return pd.DataFrame(
            {
                "cluster_id": ["c1", "c1", "c1"],
                "nombre_enfants": [1, 0, 0],
                "identifiant_unique": ["c1p", "d1", "r1"],
            }
        )

    @pytest.fixture(scope="session")
    def meta(self, df):
        return cluster_acteurs_metadata(df)

    def test_nombre_clusters(self, meta):
        # Clusters 1, 2 et 3
        assert meta[COUNT_CLUSTERS] == 1

    def test_nombre_clusters_existants(self, meta):
        # Tous les clusters sont existants sauf cluster 1
        assert meta[COUNT_CLUSTERS_CURRENT] == 1

    def test_nombre_clusters_nouveaux(self, meta):
        # Cluster 1 est nouveau
        assert meta[COUNT_CLUSTERS_NET] == 0

    def test_nombre_acteurs(self, meta):
        # 9 acteurs
        assert meta[COUNT_ACTEURS] == 3

    def test_nombre_acteurs_deja_parent(self, meta):
        # 3 acteurs déjà parent
        assert meta[COUNT_ACTEURS_CURRENT] == 2

    def test_nombre_acteurs_nouveau_enfant(self, meta):
        # 2 acteurs nouvellement clusterisés
        # = 9 - 3 déjà parents - 2 déjà clusterisés
        assert meta[COUNT_ACTEURS_NEW] == 1
