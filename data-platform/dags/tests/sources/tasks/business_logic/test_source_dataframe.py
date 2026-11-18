import numpy as np
import pandas as pd
import pytest
from sources.tasks.business_logic.source_dataframe import (
    coerce_source_dataframe_to_str,
    is_null_sentinel,
    normalize_source_nulls,
)


class TestIsNullSentinel:
    @pytest.mark.parametrize(
        "value",
        [None, np.nan, "", "None", "null", "  NONE  ", "-"],
    )
    def test_sentinels(self, value):
        assert is_null_sentinel(value) is True

    def test_real_values(self):
        assert is_null_sentinel("2026-01-01") is False
        assert is_null_sentinel(42) is False


class TestNormalizeSourceNulls:
    def test_converts_string_none_to_python_none(self):
        df = pd.DataFrame({"d": ["None", "2026-01-01", None]})
        result = normalize_source_nulls(df)
        assert result["d"].tolist() == [None, "2026-01-01", None]


class TestCoerceSourceDataframeToStr:
    def test_null_stays_none_not_string_none(self):
        df = pd.DataFrame({"id": ["1", None], "label": ["a", np.nan]})
        result = coerce_source_dataframe_to_str(df)
        assert result["id"].tolist() == ["1", None]
        assert result["label"].tolist() == ["a", None]

    def test_string_none_becomes_none(self):
        df = pd.DataFrame({"d": ["None", "2020-01-01"]})
        result = coerce_source_dataframe_to_str(df)
        assert result["d"].tolist() == [None, "2020-01-01"]
