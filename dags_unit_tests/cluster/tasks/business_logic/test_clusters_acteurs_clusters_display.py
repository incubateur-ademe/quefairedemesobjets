import pandas as pd
import pytest
from cluster.tasks.business_logic.cluster_acteurs_clusters_display import (
    cluster_acteurs_clusters_display,
)

from unit_tests.qfdmo.acteur_factory import (
    ActeurTypeFactory,
    DisplayedActeurFactory,
    SourceFactory,
)


@pytest.mark.django_db
class TestClusterActeursClustersDisplay:

    # TODO: see if we can parametrize the various tests of this class
    # to reduce length of test file
    def test_dont_fail_if_no_clusters(self):
        """Simple test but we must ensure with the growing complexity
        that we keep a core logic of no clusters = no failures thus
        the clustering function must return early with empty df"""
        at1 = ActeurTypeFactory(code="at1")
        s1 = SourceFactory(code="s1")
        DisplayedActeurFactory(identifiant_unique="p1", acteur_type=at1, ville="Paris")
        DisplayedActeurFactory(
            identifiant_unique="orphan1", acteur_type=at1, ville="Laval", source=s1
        )
        df = pd.DataFrame(
            {
                "identifiant_unique": ["p1", "orphan1"],
                "source_id": [None, s1.id],
                "acteur_type_id": [at1.id, at1.id],
                "ville": ["Paris", "Laval"],
                "__index_src": [0, 1],
                "nombre_enfants": [1, 0],
                "nom": ["p1", "orphan1"],
            }
        )

        df_clusters = cluster_acteurs_clusters_display(
            df=df,
            cluster_fields_exact=["ville"],
            cluster_fields_fuzzy=[],
            cluster_fields_separate=["source_id"],
            cluster_fuzzy_threshold=0.5,
            fields_protected=["source_id"],
            fields_transformed=["ville"],
        )
        assert df_clusters.empty

    def test_dont_fail_if_no_parents_clustered(self):
        """Issue identified on 2025-02-13 whereby IF
        clusters existed BUT no existing parents were clustered,
        we still tried to get children for the original parents
        which failed"""
        at1 = ActeurTypeFactory(code="at1")
        s1 = SourceFactory(code="s1")
        s2 = SourceFactory(code="s2")
        DisplayedActeurFactory(identifiant_unique="p1", acteur_type=at1, ville="Paris")
        DisplayedActeurFactory(
            identifiant_unique="orphan1", acteur_type=at1, ville="Laval", source=s1
        )
        DisplayedActeurFactory(
            identifiant_unique="orphan2", acteur_type=at1, ville="Laval", source=s2
        )
        df = pd.DataFrame(
            {
                "identifiant_unique": ["p1", "orphan1", "orphan2"],
                "source_id": [None, s1.id, s2.id],
                "acteur_type_id": [at1.id, at1.id, at1.id],
                "ville": ["Paris", "Laval", "Laval"],
                "__index_src": [0, 1, 2],
                "nombre_enfants": [1, 0, 0],
                "nom": ["p1", "orphan1", "orphan2"],
            }
        )

        df_clusters = cluster_acteurs_clusters_display(
            df=df,
            cluster_fields_exact=["ville"],
            cluster_fields_fuzzy=[],
            cluster_fields_separate=["source_id"],
            cluster_fuzzy_threshold=0.5,
            fields_protected=["source_id"],
            fields_transformed=["ville"],
        )
        assert len(df_clusters) == 2
        assert df_clusters["cluster_id"].nunique() == 1
