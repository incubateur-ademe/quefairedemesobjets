import pandas as pd
import pytest
from cluster.config.constants import COL_PARENT_DATA_NEW
from cluster.tasks.airflow_logic.utils import (
    parent_data_new_deserialize,
    parent_data_new_serialize,
)
from cluster.tasks.business_logic.cluster_acteurs_suggestions.prepare import (
    cluster_acteurs_suggestions_prepare,
)
from data.models.change import (
    COL_CHANGE_MODEL_NAME,
    COL_CHANGE_ORDER,
    COL_CHANGE_REASON,
)
from django.contrib.gis.geos import Point
from unit_tests.qfdmo.acteur_factory import ActeurTypeFactory


@pytest.mark.django_db
class TestParentDataNewSerde:

    def test_roundtrip_preserves_dicts_empty_and_none(self):
        # The empty dict is the case that breaks Parquet XCom serialization
        df = pd.DataFrame(
            {
                "identifiant_unique": ["p1", "p2", "a1"],
                COL_PARENT_DATA_NEW: [{"nom": "new"}, {}, None],
            }
        )

        serialized = parent_data_new_serialize(df)
        # On the wire the column is JSON strings (or None), never dicts
        assert serialized[COL_PARENT_DATA_NEW].tolist() == [
            '{"nom": "new"}',
            "{}",
            None,
        ]

        restored = parent_data_new_deserialize(serialized)
        assert restored[COL_PARENT_DATA_NEW].tolist() == [{"nom": "new"}, {}, None]

    def test_all_empty_dicts_serialize_to_strings(self):
        # All-empty case is exactly what raised ArrowNotImplementedError
        df = pd.DataFrame({COL_PARENT_DATA_NEW: [{}, {}]})
        serialized = parent_data_new_serialize(df)
        assert serialized[COL_PARENT_DATA_NEW].tolist() == ["{}", "{}"]
        assert parent_data_new_deserialize(serialized)[
            COL_PARENT_DATA_NEW
        ].tolist() == [
            {},
            {},
        ]

    def test_noop_when_column_absent(self):
        df = pd.DataFrame({"identifiant_unique": ["p1"]})
        assert parent_data_new_serialize(df).equals(df)
        assert parent_data_new_deserialize(df).equals(df)

    def test_roundtrip_preserves_point_location_as_coords(self):
        df = pd.DataFrame(
            {
                COL_PARENT_DATA_NEW: [
                    {"nom": "EPUR CENTRE", "location": Point(3.447635, 46.1413235)}
                ]
            }
        )

        serialized = parent_data_new_serialize(df)
        assert serialized[COL_PARENT_DATA_NEW].iloc[0] == (
            '{"nom": "EPUR CENTRE", "location": [3.447635, 46.1413235]}'
        )

        restored = parent_data_new_deserialize(serialized)
        assert restored[COL_PARENT_DATA_NEW].iloc[0] == {
            "nom": "EPUR CENTRE",
            "location": [3.447635, 46.1413235],
        }

    def test_roundtrip_preserves_acteur_type_as_code(self):
        acteur_type = ActeurTypeFactory(code="decheterie", libelle="déchèterie")
        df = pd.DataFrame(
            {
                COL_PARENT_DATA_NEW: [{"acteur_type": acteur_type}],
            }
        )

        restored = parent_data_new_deserialize(parent_data_new_serialize(df))
        assert restored[COL_PARENT_DATA_NEW].iloc[0] == {"acteur_type": "decheterie"}

    def test_xcom_roundtrip_acteur_type_survives_suggestions_prepare(self):
        acteur_type = ActeurTypeFactory(code="decheterie", libelle="déchèterie")
        df = pd.DataFrame(
            [
                {
                    "cluster_id": "c1",
                    "identifiant_unique": "new parent",
                    COL_CHANGE_ORDER: 1,
                    COL_CHANGE_REASON: "because",
                    COL_CHANGE_MODEL_NAME: "acteur_create_as_parent",
                    COL_PARENT_DATA_NEW: {
                        "acteur_type": acteur_type,
                        "location": Point(3.447635, 46.1413235),
                    },
                }
            ]
        )

        df = parent_data_new_deserialize(parent_data_new_serialize(df))
        working, failing = cluster_acteurs_suggestions_prepare(df)

        assert failing == []
        data = working[0]["changes"][0]["model_params"]["data"]
        assert data["acteur_type"] == "decheterie"
        assert data["longitude"] == 3.447635
        assert data["latitude"] == 46.1413235
