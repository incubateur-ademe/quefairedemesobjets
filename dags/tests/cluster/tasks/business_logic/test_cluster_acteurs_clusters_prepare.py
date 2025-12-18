import pandas as pd
import pytest
from cluster.tasks.business_logic.cluster_acteurs_clusters_prepare import (
    cluster_acteurs_clusters_prepare,
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
        s2 = SourceFactory(code="s2")
        DisplayedActeurFactory(identifiant_unique="p1", acteur_type=at1, ville="Paris")
        DisplayedActeurFactory(
            identifiant_unique="orphan1", acteur_type=at1, ville="Laval", source=s1
        )
        df = pd.DataFrame(
            {
                "identifiant_unique": ["p1", "orphan1"],
                "source_id": [None, s1.id],
                "source_code": [None, s1.code],
                "source_codes": [[s1.code, s2.code], [s1.code]],
                "acteur_type_id": [at1.id, at1.id],
                "ville": ["Paris", "Laval"],
                "nombre_enfants": [1, 0],
                "nom": ["p1", "orphan1"],
            }
        )

        df_clusters = cluster_acteurs_clusters_prepare(
            df=df,
            cluster_fields_exact=["ville"],
            cluster_fields_fuzzy=[],
            cluster_fuzzy_threshold=0.5,
            cluster_intra_source_is_allowed=False,
            fields_protected=["source_id"],
            fields_transformed=["ville"],
            include_source_ids=[s1.id, s2.id],
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
                "source_code": [None, s1.code, s2.code],
                "source_codes": [[s1.code, s2.code], [s1.code], [s2.code]],
                "acteur_type_id": [at1.id, at1.id, at1.id],
                "ville": ["Paris", "Laval", "Laval"],
                "nombre_enfants": [1, 0, 0],
                "nom": ["p1", "orphan1", "orphan2"],
            }
        )

        df_clusters = cluster_acteurs_clusters_prepare(
            df=df,
            cluster_fields_exact=["ville"],
            cluster_fields_fuzzy=[],
            cluster_fuzzy_threshold=0.5,
            cluster_intra_source_is_allowed=False,
            fields_protected=["source_id"],
            fields_transformed=["ville"],
            include_source_ids=[s1.id, s2.id],
        )
        assert len(df_clusters) == 2
        assert df_clusters["cluster_id"].nunique() == 1

    def test_remove_clusters_without_included_sources(self):
        at1 = ActeurTypeFactory(code="at1")
        s_included = SourceFactory(code="s_included")
        s_excluded_1 = SourceFactory(code="s_excluded_1")
        s_excluded_2 = SourceFactory(code="s_excluded_2")

        DisplayedActeurFactory(
            identifiant_unique="clusterA_1",
            acteur_type=at1,
            ville="Paris",
            source=s_included,
        )
        DisplayedActeurFactory(
            identifiant_unique="clusterA_2",
            acteur_type=at1,
            ville="Paris",
            source=s_excluded_1,
        )
        DisplayedActeurFactory(
            identifiant_unique="clusterB_1",
            acteur_type=at1,
            ville="Lyon",
            source=s_excluded_1,
        )
        DisplayedActeurFactory(
            identifiant_unique="clusterB_2",
            acteur_type=at1,
            ville="Lyon",
            source=s_excluded_2,
        )

        df = pd.DataFrame(
            {
                "identifiant_unique": [
                    "clusterA_1",
                    "clusterA_2",
                    "clusterB_1",
                    "clusterB_2",
                ],
                "source_id": [
                    s_included.id,
                    s_excluded_1.id,
                    s_excluded_1.id,
                    s_excluded_2.id,
                ],
                "source_code": [
                    s_included.code,
                    s_excluded_1.code,
                    s_excluded_1.code,
                    s_excluded_2.code,
                ],
                "source_codes": [
                    [s_included.code],
                    [s_excluded_1.code],
                    [s_excluded_1.code],
                    [s_excluded_2.code],
                ],
                "acteur_type_id": [at1.id, at1.id, at1.id, at1.id],
                "ville": ["Paris", "Paris", "Lyon", "Lyon"],
                "nombre_enfants": [0, 0, 0, 0],
                "nom": ["clusterA_1", "clusterA_2", "clusterB_1", "clusterB_2"],
            }
        )

        df_clusters = cluster_acteurs_clusters_prepare(
            df=df,
            cluster_fields_exact=["ville"],
            cluster_fields_fuzzy=[],
            cluster_fuzzy_threshold=0.5,
            cluster_intra_source_is_allowed=False,
            fields_protected=["source_id"],
            fields_transformed=["ville"],
            include_source_ids=[s_included.id],
        )

        assert df_clusters["cluster_id"].nunique() == 1
        assert set(df_clusters["identifiant_unique"]) == {"clusterA_1", "clusterA_2"}
