import pytest

from dags.shared.tasks.business_logic.normalize import (
    string_basic,
    string_order_unique_words,
    string_remove_small_words,
)


class TestNormalizeStrings:

    @pytest.mark.parametrize(
        "input,expected",
        [
            (" LE PETIT CHAT ! ", "le petit chat"),
            (" Château de l'île", "chateau de l ile"),
            (" foo & bar ", "foo bar"),
            ("", ""),
            (None, ""),
            # Conversion des types non-chaines mais
            # sans se faire avoir avec les valeurs qui
            # évaluent à False
            (False, "false"),
            (123, "123"),
            (0, "0"),
        ],
    )
    def test_string_basic(self, input, expected):
        assert string_basic(input) == expected

    @pytest.mark.parametrize(
        "input,size,expected",
        [
            ("a b c", 1, ""),
            ("aa b cc", 1, "aa cc"),
            ("ccc b aaa", 2, "ccc aaa"),
            ("", 1, ""),
            (None, 1, ""),
            (1, 1, ""),
            (123, 1, "123"),
        ],
    )
    def test_string_remove_small_words(self, input, size, expected):
        assert string_remove_small_words(input, size) == expected

    @pytest.mark.parametrize(
        "input,expected",
        [
            ("c b a", "a b c"),
            ("rue rue leon gautier", "gautier leon rue"),
            ("rue de de paris paris", "de paris rue"),
            ("", ""),
            (None, ""),
            (123, "123"),
        ],
    )
    def test_string_order_unique_words(self, input, expected):
        assert string_order_unique_words(input) == expected
