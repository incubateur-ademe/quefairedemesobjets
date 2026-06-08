import pandas as pd
from cluster.config.constants import COL_PARENT_DATA_NEW
from cluster.tasks.business_logic.misc.parent_data_serde import (
    parent_data_new_deserialize,
    parent_data_new_serialize,
)


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
