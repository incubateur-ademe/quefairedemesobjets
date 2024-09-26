from unittest.mock import patch

import pandas as pd
from utils.base_utils import get_address
from utils.mapping_utils import parse_float


def mock_get_address_from_ban(address):
    return {
        "latitude": 48.8566,
        "longitude": 2.3522,
        "query": address,
        "label": "Mocked Label",
        "address": "Mocked Address",
        "postal_code": "75001",
        "city": "Paris",
        "match_percentage": 85,
    }


class TestGetAddress:
    @patch(
        "utils.base_utils.get_address_from_ban",
        side_effect=mock_get_address_from_ban,
    )
    def test_get_address(self, mock_get_address):
        data = {"adresse_format_ban": ["123 Mocked St 75001 Paris"]}
        df = pd.DataFrame(data)

        expected_output = pd.Series(["Mocked Address", "75001", "Paris"])
        result = get_address(df.iloc[0])
        pd.testing.assert_series_equal(result, expected_output)

    @patch(
        "utils.base_utils.get_address_from_ban",
        side_effect=mock_get_address_from_ban,
    )
    def test_get_address_with_null(self, mock_get_address):
        data = {"adresse_format_ban": [None]}
        df = pd.DataFrame(data)
        expected_output = pd.Series([None, None, None])
        result = get_address(df.iloc[0])
        pd.testing.assert_series_equal(result, expected_output)

    @patch(
        "utils.base_utils.get_address_from_ban",
        side_effect=mock_get_address_from_ban,
    )
    def test_get_address_below_threshold(self, mock_get_address):
        data = {"adresse_format_ban": ["10 passage saint ambroise 75011 Paris"]}
        df = pd.DataFrame(data)

        with patch("utils.base_utils.get_address_from_ban") as mock_method:
            mock_method.return_value = {
                "match_percentage": 49,  # Below threshold
                "address": None,
                "postal_code": None,
                "city": None,
            }

            expected_output = pd.Series(["10 passage saint ambroise", "75011", "Paris"])
            result = get_address(df.iloc[0])
            pd.testing.assert_series_equal(result, expected_output)


class TestParseFloat:
    def test_parse_float_with_french_decimal(self):
        assert parse_float("1234,56") == 1234.56
        assert parse_float("-1234,56") == -1234.56
        assert parse_float("0,0") == 0
        assert parse_float("1,234") == 1.234

    def test_parse_float_with_trailing_comma(self):
        assert parse_float("1234,") == 1234.0
        assert parse_float("1234,56,") == 1234.56

    def test_parse_float_with_valid_float(self):
        assert parse_float(1234.56) == 1234.56
        assert parse_float(-1234.56) == -1234.56

    def test_parse_float_with_nan(self):
        assert parse_float(float("nan")) is None

    def test_parse_float_with_none(self):
        assert parse_float(None) is None

    def test_parse_float_with_invalid_string(self):
        assert parse_float("abc") is None
        assert parse_float("1234abc") is None
        assert parse_float("12,34,56") is None
