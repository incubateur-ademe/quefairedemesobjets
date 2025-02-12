import pandas as pd
import pytest
from cluster.tasks.business_logic.misc.df_metadata_get import (
    COUNT_ACTEURS,
    COUNT_ACTEURS_CURRENT,
    COUNT_ACTEURS_NEW,
    COUNT_CLUSTERS,
    COUNT_CLUSTERS_CURRENT,
    COUNT_CLUSTERS_NET,
    df_metadata_get,
)


class TestClusterActeursMetadata:

    @pytest.fixture(scope="session")
    def df(self):
        return pd.DataFrame(
            [
                # Cluster 1 = 1 parent w/ 1 rev + 1 new child
                ["c1", 1, "c1p"],
                ["c1", 0, "c1d1"],
                ["c1", 0, "c1r1"],
                # Cluster 2 = 2 parents w/ 3,2 rev + 4 new children
                ["c2", 3, "c2p1"],
                ["c2", 2, "c2p2"],
                ["c2", 0, "c2p1r1"],
                ["c2", 0, "c2p1r2"],
                ["c2", 0, "c2p1r3"],
                ["c2", 0, "c2p2r1"],
                ["c2", 0, "c2p2r2"],
                ["c2", 0, "c2d1"],
                ["c2", 0, "c2d2"],
                ["c2", 0, "c2d3"],
                ["c2", 0, "c2d4"],
            ],
            columns=["cluster_id", "nombre_enfants", "identifiant_unique"],
        )

    @pytest.fixture(scope="session")
    def meta(self, df):
        return df_metadata_get(df)

    def test_nombre_clusters(self, meta):
        # Clusters 1 & 2
        assert meta[COUNT_CLUSTERS] == 2

    def test_nombre_clusters_existants(self, meta):
        # # parent existants = # clusters existants
        assert meta[COUNT_CLUSTERS_CURRENT] == 3

    def test_nombre_clusters_nouveaux(self, meta):
        # Normal d'avoir -1 car on a moins de
        # clusters que de parents existants
        assert meta[COUNT_CLUSTERS_NET] == -1

    def test_nombre_acteurs(self, meta):
        # Tous les enfants + orphelins
        assert meta[COUNT_ACTEURS] == 11

    def test_nombre_acteurs_deja_parent(self, meta):
        assert meta[COUNT_ACTEURS_CURRENT] == 6

    def test_nombre_acteurs_nouveau_enfant(self, meta):
        assert meta[COUNT_ACTEURS_NEW] == 5
