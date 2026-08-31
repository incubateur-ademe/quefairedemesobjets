import pandas as pd
from sources.tasks.business_logic.source_data_download import (
    drop_rows_with_null_or_empty_fields,
)


class TestDropRowsWithNullFields:
    def test_noop_when_fields_empty(self):
        data = [{"id": 1}, {"id": None}, {"id": ""}]
        assert drop_rows_with_null_or_empty_fields(data, []) == data
        assert drop_rows_with_null_or_empty_fields(data, None) == data

    def test_filters_list_of_dicts(self):
        data = [
            {"id": 1, "nom": "a"},
            {"id": None, "nom": "b"},
            {"id": 3, "nom": None},
            {"id": 4, "nom": "d"},
            {"id": 5, "nom": ""},
        ]
        filtered = drop_rows_with_null_or_empty_fields(data, ["id", "nom"])
        assert filtered == [
            {"id": 1, "nom": "a"},
            {"id": 4, "nom": "d"},
        ]

    def test_warns_on_dataframe(self, caplog):
        df = pd.DataFrame([{"id": 1}])
        with caplog.at_level("WARNING"):
            filtered = drop_rows_with_null_or_empty_fields(df, ["id"])
        assert len(filtered) == 1
        assert "is not applied on a DataFrame" in caplog.text
