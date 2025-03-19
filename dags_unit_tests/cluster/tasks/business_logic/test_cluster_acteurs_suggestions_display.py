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
from shapely.geometry import Point

from dags.cluster.tasks.business_logic.cluster_acteurs_suggestions.display import (
    cluster_acteurs_suggestions_display,
)
from data.models.change import (
    COL_CHANGE_ENTITY_TYPE,
    COL_CHANGE_MODEL_NAME,
    COL_CHANGE_ORDER,
    COL_CHANGE_REASON,
    ENTITY_ACTEUR_DISPLAYED,
    ENTITY_ACTEUR_REVISION,
    ENTITY_ACTEUR_TO_CREATE,
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
        """Intentionally creating technically invalid clusters
        to demonstrate that at this point the suggestions task
        no longer performs cluster-wide validation, it just looks
        at individual changes"""

        # However we must have valid data in DB as validations
        # are validated
        DisplayedActeurFactory(id="parent to delete")
        DisplayedActeurFactory(id="parent to keep")
        RevisionActeurFactory(id="parent to keep")
        RevisionActeurFactory(id="revision to keep")
        ActeurFactory(id="update parent id")
        RevisionActeurFactory(id="update parent id")
        at1 = ActeurTypeFactory(code="at1", id=ACTEUR_TYPE_ID)

        return pd.DataFrame(
            [
                {
                    "cluster_id": "c1",
                    "id": "new parent",
                    "parent_id": None,
                    COL_CHANGE_ORDER: 1,
                    COL_CHANGE_REASON: "because",
                    COL_CHANGE_ENTITY_TYPE: ENTITY_ACTEUR_TO_CREATE,
                    COL_CHANGE_MODEL_NAME: CHANGE_CREATE,
                    COL_PARENT_DATA_NEW: {"acteur_type": at1, "location": Point(1, 2)},
                },
                {
                    "cluster_id": "c1",
                    "id": "parent to delete",
                    "parent_id": None,
                    COL_CHANGE_ORDER: 1,
                    COL_CHANGE_REASON: "because",
                    COL_CHANGE_ENTITY_TYPE: ENTITY_ACTEUR_DISPLAYED,
                    COL_CHANGE_MODEL_NAME: CHANGE_DELETE,
                    COL_PARENT_DATA_NEW: None,
                },
                {
                    "cluster_id": "c2",
                    "id": "parent to keep",
                    "parent_id": None,
                    COL_CHANGE_ORDER: 1,
                    COL_CHANGE_REASON: "because",
                    COL_CHANGE_ENTITY_TYPE: ENTITY_ACTEUR_DISPLAYED,
                    COL_CHANGE_MODEL_NAME: CHANGE_KEEP,
                    COL_PARENT_DATA_NEW: {"acteur_type": at1},
                },
                {
                    "cluster_id": "c3",
                    "id": "revision to keep",
                    "parent_id": "parent to keep",
                    COL_CHANGE_ORDER: 1,
                    COL_CHANGE_REASON: "because",
                    COL_CHANGE_ENTITY_TYPE: ENTITY_ACTEUR_REVISION,
                    COL_CHANGE_MODEL_NAME: CHANGE_NOTHING,
                    COL_PARENT_DATA_NEW: None,
                },
                {
                    "cluster_id": "c3",
                    "id": "update parent id",
                    "parent_id": "parent to keep",
                    COL_CHANGE_ORDER: 1,
                    COL_CHANGE_REASON: "because",
                    COL_CHANGE_ENTITY_TYPE: ENTITY_ACTEUR_REVISION,
                    COL_CHANGE_MODEL_NAME: CHANGE_POINT,
                    COL_PARENT_DATA_NEW: None,
                },
            ]
        )

    @pytest.fixture
    def suggestions(self, df_clusters):
        # The function should have everything it needs from the df
        return cluster_acteurs_suggestions_display(df_clusters)

    def test_structure_and_type(self, suggestions):
        assert isinstance(suggestions, list)
        assert isinstance(suggestions[0], dict)
        assert list(suggestions[0].keys()) == ["cluster_id", "changes"]
        assert isinstance(suggestions[0]["cluster_id"], str)
        assert isinstance(suggestions[0]["changes"], list)
        assert isinstance(suggestions[0]["changes"][0], dict)

    def test_one_suggestion_per_cluster(self, df_clusters, suggestions):
        assert len(suggestions) == df_clusters["cluster_id"].nunique()

    def test_verify_clusters(self, suggestions):
        assert suggestions[0]["cluster_id"] == "c1"
        assert suggestions[1]["cluster_id"] == "c2"
        assert suggestions[2]["cluster_id"] == "c3"

    def test_model_params_location_converted(self, suggestions):
        c1 = suggestions[0]
        data = c1["changes"][0]["model_params"]["data"]
        assert "location" not in data
        assert data["longitude"] == 1.0
        assert data["latitude"] == 2.0

    def test_verify_model_params(self, suggestions):
        c1 = suggestions[0]
        assert c1["changes"][0]["model_params"] == {
            "id": "new parent",
            "data": {"acteur_type": ACTEUR_TYPE_ID, "longitude": 1.0, "latitude": 2.0},
        }
        assert c1["changes"][1]["model_params"] == {"id": "parent to delete"}

        c2 = suggestions[1]
        assert c2["changes"][0]["model_params"] == {
            "id": "parent to keep",
            "data": {"acteur_type": ACTEUR_TYPE_ID},
        }

        c3 = suggestions[2]
        assert c3["changes"][0]["model_params"] == {"id": "revision to keep"}
        assert c3["changes"][1]["model_params"] == {
            "id": "update parent id",
            "data": {"parent_id": "parent to keep"},
        }
