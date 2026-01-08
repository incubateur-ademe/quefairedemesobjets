import pandas as pd
import pytest
from cluster.tasks.business_logic.cluster_acteurs_clusters_validate import (
    cluster_acteurs_clusters_validate,
)


class TestClusterActeursSuggestionsValidate:
    def test_issue_clusters_size1(self):
        df = pd.DataFrame(
            {
                "statut": ["ACTIF"],
                "cluster_id": ["I am alone"],
                "identifiant_unique": ["A"],
            }
        )
        with pytest.raises(ValueError, match="Clusters avec moins de 2 acteurs"):
            cluster_acteurs_clusters_validate(df)

    def test_issue_acteurs_defined_multiple_times_same_cluster(self):
        # Que l'acteur en question soit répété dans le même cluster
        df = pd.DataFrame(
            {
                "identifiant_unique": ["A", "A"],
                "statut": ["ACTIF", "ACTIF"],
                "cluster_id": ["1", "1"],
            }
        )
        with pytest.raises(ValueError, match="Acteurs définis plusieurs fois"):
            cluster_acteurs_clusters_validate(df)

    def test_issue_acteurs_defined_multiple_times_different_clusters(self):
        # Que l'acteur en question soit répété dans différents clusters
        df = pd.DataFrame(
            {
                "identifiant_unique": ["A", "A", "B", "C"],
                "statut": ["ACTIF", "ACTIF", "ACTIF", "ACTIF"],
                "cluster_id": ["1", "2", "1", "2"],
            }
        )
        with pytest.raises(ValueError, match="Acteurs définis plusieurs fois"):
            cluster_acteurs_clusters_validate(df)

    def test_issue_cluster_ids_not_ordered(self):
        # Des cluster_ids non ordonnés (par convention de manière croissante)
        # sont peut-être le signe d'un problème de logique ou de collisions
        # des IDs
        df = pd.DataFrame(
            {
                "identifiant_unique": ["A", "B", "C", "D"],
                "statut": ["ACTIF", "ACTIF", "ACTIF", "ACTIF"],
                "cluster_id": ["1", "2", "1", "2"],
            }
        )
        with pytest.raises(ValueError, match="Cluster IDs non ordonnés"):
            cluster_acteurs_clusters_validate(df)

    def test_working_case(self):
        df = pd.DataFrame(
            {
                "identifiant_unique": ["A", "B", "C", "D"],
                "statut": ["ACTIF", "ACTIF", "ACTIF", "ACTIF"],
                "cluster_id": ["1", "1", "2", "2"],
            }
        )
        cluster_acteurs_clusters_validate(df)
