import pytest
from sources.tasks.airflow_logic.config_management import get_nested_config_parameter


@pytest.mark.parametrize(
    "input_value, expected_output",
    [
        # chaine vide
        ("", ""),
        # String
        ("simple string", "simple string"),
        # Dict
        ("{'key': 'value'}", {"key": "value"}),
        ('{"key": "value"}', {"key": "value"}),
        # List
        ("['simple string1', 'simple string2']", ["simple string1", "simple string2"]),
        ('["simple string1", "simple string2"]', ["simple string1", "simple string2"]),
        # Nested
        (
            "{'key1': ['simple string1', 'simple string2'], 'key2': 'value2'}",
            {"key1": ["simple string1", "simple string2"], "key2": "value2"},
        ),
        (
            "[{'key': 'value'}, 'simple string2']",
            [{"key": "value"}, "simple string2"],
        ),
    ],
)
def test_get_nested_config_parameter(input_value, expected_output):
    assert get_nested_config_parameter(input_value) == expected_output


def test_get_nested_config_parameter_none():
    with pytest.raises(ValueError):
        get_nested_config_parameter(None)  # type: ignore
