import pandas as pd
import pytest
from cluster.config.constants import COL_PARENT_DATA_NEW
from cluster.helpers.shorthands.change_model_name import (
    CHANGE_CREATE,
    CHANGE_DELETE,
    CHANGE_KEEP,
    CHANGE_NOTHING,
    CHANGE_POINT,
)
from cluster.tasks.business_logic.cluster_acteurs_suggestions.prepare import (
    cluster_acteurs_suggestions_prepare,
)
from shapely.geometry import Point

from data.models.change import (
    COL_CHANGE_MODEL_NAME,
    COL_CHANGE_ORDER,
    COL_CHANGE_REASON,
)
from unit_tests.qfdmo.acteur_factory import (
    ActeurFactory,
    ActeurTypeFactory,
    DisplayedActeurFactory,
    RevisionActeurFactory,
)

ACTEUR_TYPE_ID = 123456


@pytest.mark.django_db
class TestClusterActeursSuggestionsDisplay:

    @pytest.fixture
    def df_clusters(self):
        # Cluster data used for tests, presence of data needed in DB
        # as prepare task does some DB validation
        DisplayedActeurFactory(identifiant_unique="parent to delete")
        DisplayedActeurFactory(identifiant_unique="parent to keep")
        RevisionActeurFactory(identifiant_unique="parent to keep")
        RevisionActeurFactory(identifiant_unique="revision to keep")
        ActeurFactory(identifiant_unique="update parent id")
        RevisionActeurFactory(identifiant_unique="update parent id")
        at1 = ActeurTypeFactory(code="at1", id=ACTEUR_TYPE_ID)

        return pd.DataFrame(
            [
                {
                    "cluster_id": "c1",
                    "identifiant_unique": "new parent",
                    "parent_id": None,
                    COL_CHANGE_ORDER: 1,
                    COL_CHANGE_REASON: "because",
                    COL_CHANGE_MODEL_NAME: CHANGE_CREATE,
                    COL_PARENT_DATA_NEW: {"acteur_type": at1, "location": Point(1, 2)},
                },
                {
                    "cluster_id": "c1",
                    "identifiant_unique": "parent to delete",
                    "parent_id": None,
                    COL_CHANGE_ORDER: 1,
                    COL_CHANGE_REASON: "because",
                    COL_CHANGE_MODEL_NAME: CHANGE_DELETE,
                    COL_PARENT_DATA_NEW: None,
                },
                {
                    "cluster_id": "c2",
                    "identifiant_unique": "parent to keep",
                    "parent_id": None,
                    COL_CHANGE_ORDER: 1,
                    COL_CHANGE_REASON: "because",
                    COL_CHANGE_MODEL_NAME: CHANGE_KEEP,
                    COL_PARENT_DATA_NEW: {"acteur_type": at1},
                },
                {
                    "cluster_id": "c3",
                    "identifiant_unique": "revision to keep",
                    "parent_id": "parent to keep",
                    COL_CHANGE_ORDER: 1,
                    COL_CHANGE_REASON: "because",
                    COL_CHANGE_MODEL_NAME: CHANGE_NOTHING,
                    COL_PARENT_DATA_NEW: None,
                },
                {
                    "cluster_id": "c3",
                    "identifiant_unique": "update parent id",
                    "parent_id": "parent to keep",
                    COL_CHANGE_ORDER: 1,
                    COL_CHANGE_REASON: "because",
                    COL_CHANGE_MODEL_NAME: CHANGE_POINT,
                    COL_PARENT_DATA_NEW: None,
                },
                # A failing cluster:
                # - the parent creation in itself is good
                # - however there is a typo in the parent id of the child to attach
                # Thus the entire cluster should be rejected
                {
                    "cluster_id": "c4",
                    "identifiant_unique": "c4 new parent",
                    "parent_id": None,
                    COL_CHANGE_ORDER: 1,
                    COL_CHANGE_REASON: "because",
                    COL_CHANGE_MODEL_NAME: CHANGE_CREATE,
                    COL_PARENT_DATA_NEW: {"acteur_type": at1, "location": Point(1, 2)},
                },
                {
                    "cluster_id": "c4",
                    "identifiant_unique": "🔴🔴🔴 c4 child FORGOT TO CREATE 🔴🔴🔴",
                    "parent_id": "c4 new parent",
                    COL_CHANGE_ORDER: 1,
                    COL_CHANGE_REASON: "attach to parent c4",
                    COL_CHANGE_MODEL_NAME: CHANGE_POINT,
                    COL_PARENT_DATA_NEW: None,
                },
            ]
        )

    @pytest.fixture
    def suggestions(self, df_clusters):
        working, failing = cluster_acteurs_suggestions_prepare(df_clusters)
        return working, failing

    @pytest.fixture
    def working(self, suggestions):
        return suggestions[0]

    @pytest.fixture
    def failing(self, suggestions):
        return suggestions[1]

    def test_structure_and_type(self, working):
        assert isinstance(working, list)
        assert isinstance(working[0], dict)
        assert list(working[0].keys()) == ["title", "cluster_id", "changes"]

    def test_one_suggestion_per_cluster(self, df_clusters, working):
        # 1 suggestion per cluster EXCEPT for failing c4
        assert len(working) == df_clusters["cluster_id"].nunique() - 1

    def test_verify_clusters(self, working):
        assert working[0]["cluster_id"] == "c1"
        assert working[1]["cluster_id"] == "c2"
        assert working[2]["cluster_id"] == "c3"

    def test_model_params_location_converted(self, working):
        c1 = working[0]
        data = c1["changes"][0]["model_params"]["data"]
        assert "location" not in data
        assert data["longitude"] == 1.0
        assert data["latitude"] == 2.0

    def test_verify_model_params(self, working):
        c1 = working[0]
        assert c1["changes"][0]["model_params"] == {
            "id": "new parent",
            "data": {"acteur_type": ACTEUR_TYPE_ID, "longitude": 1.0, "latitude": 2.0},
        }
        assert c1["changes"][1]["model_params"] == {"id": "parent to delete"}

        c2 = working[1]
        assert c2["changes"][0]["model_params"] == {
            "id": "parent to keep",
            "data": {"acteur_type": ACTEUR_TYPE_ID},
        }

        c3 = working[2]
        assert c3["changes"][0]["model_params"] == {"id": "revision to keep"}
        assert c3["changes"][1]["model_params"] == {
            "id": "update parent id",
            "data": {"parent_id": "parent to keep"},
        }

    def test_failing_clusters(self, working, failing):
        # The entire cluster c4 should be rejected
        assert len(failing) == 1
        assert failing[0]["cluster_id"] == "c4"
        assert "Acteur matching query does not exist" in failing[0]["error"]

        # We should find no trace of c4 in the working suggestions
        assert "c4" not in [x["cluster_id"] for x in working]
