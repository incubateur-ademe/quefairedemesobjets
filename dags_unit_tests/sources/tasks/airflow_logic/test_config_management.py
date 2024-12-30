import pytest
from sources.tasks.airflow_logic.config_management import (
    DAGConfig,
    NormalizationColumnDefault,
    NormalizationColumnKeep,
    NormalizationColumnRemove,
    NormalizationColumnRename,
    NormalizationColumnTransform,
    NormalizationDFTransform,
    get_nested_config_parameter,
)


class TestGetNestedConfigParameter:
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
            (
                "['simple string1', 'simple string2']",
                ["simple string1", "simple string2"],
            ),
            (
                '["simple string1", "simple string2"]',
                ["simple string1", "simple string2"],
            ),
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
    def test_get_nested_config_parameter(self, input_value, expected_output):
        assert get_nested_config_parameter(input_value) == expected_output

    def test_get_nested_config_parameter_none(self):
        with pytest.raises(ValueError):
            get_nested_config_parameter(None)  # type: ignore


class TestDAGConfig:
    def test_dag_config_success(self):
        dag_config = DAGConfig.model_validate(
            {
                "column_transformations": [],
                "endpoint": "https://example.com/api",
                "product_mapping": {},
            }
        )
        assert str(dag_config.endpoint) == "https://example.com/api"
        assert dag_config.column_transformations == []
        assert dag_config.combine_columns_categories == []
        assert dag_config.dechet_mapping == {}
        assert dag_config.ignore_duplicates is False
        assert dag_config.label_bonus_reparation is None
        assert dag_config.merge_duplicated_acteurs is False
        assert dag_config.product_mapping == {}
        assert dag_config.source_code is None
        assert dag_config.validate_address_with_ban is False

    @pytest.mark.parametrize(
        "input_value",
        [
            {},
            {
                "column_transformations": "not_a_list",
                "endpoint": "https://example.com/api",
                "product_mapping": {},
            },
            {
                "column_transformations": [],
                "endpoint": "https://example.com/api",
                "product_mapping": "not_a_dict",
            },
            {
                "column_transformations": [],
                "endpoint": "not_an_url",
                "product_mapping": {},
            },
            {
                "column_transformations": [{"fake": "column"}],
                "endpoint": "not_an_url",
                "product_mapping": {},
            },
        ],
    )
    def test_dag_config_fail(self, input_value):
        with pytest.raises(ValueError):
            DAGConfig.model_validate(input_value)

    @pytest.mark.parametrize(
        "column_transformations, expected_column_transformations",
        [
            ([], []),
            (
                [{"origin": "orig", "destination": "dest"}],
                [NormalizationColumnRename(origin="orig", destination="dest")],
            ),
            (
                [{"origin": "orig", "transformation": "trans", "destination": "dest"}],
                [
                    NormalizationColumnTransform(
                        origin="orig", transformation="trans", destination="dest"
                    )
                ],
            ),
            (
                [{"column": "col", "value": "val"}],
                [NormalizationColumnDefault(column="col", value="val")],
            ),
            (
                [
                    {
                        "origin": ["orig"],
                        "transformation": "trans",
                        "destination": ["dest"],
                    }
                ],
                [
                    NormalizationDFTransform(
                        origin=["orig"], transformation="trans", destination=["dest"]
                    )
                ],
            ),
            ([{"remove": "column"}], [NormalizationColumnRemove(remove="column")]),
            ([{"keep": "column"}], [NormalizationColumnKeep(keep="column")]),
        ],
    )
    def test_dag_config_column_transformations_succeed(
        self, column_transformations, expected_column_transformations
    ):
        dag_config = DAGConfig.model_validate(
            {
                "column_transformations": column_transformations,
                "endpoint": "https://example.com/api",
                "product_mapping": {},
            }
        )
        assert dag_config.column_transformations == expected_column_transformations

    @pytest.mark.parametrize(
        "column_transformations",
        [
            [{"fake": "column"}],
            [{"origin": ["orig"], "transformation": "trans", "destination": "dest"}],
            [{"origin": "orig", "transformation": "trans", "destination": ["dest"]}],
        ],
    )
    def test_dag_config_column_transformations_failed(self, column_transformations):
        with pytest.raises(ValueError):
            DAGConfig.model_validate(
                {
                    "column_transformations": column_transformations,
                    "endpoint": "https://example.com/api",
                    "product_mapping": {},
                }
            )

    def test_get_expected_columns(self):
        column_transformations = [
            NormalizationColumnRename(origin="orig", destination="dest1"),
            NormalizationColumnTransform(
                origin="orig", transformation="", destination="dest2"
            ),
            NormalizationDFTransform(
                origin=["orig"], transformation="", destination=["dest3"]
            ),
            NormalizationColumnDefault(column="col", value="val"),
            NormalizationColumnKeep(keep="keep"),
        ]
        dag_config = DAGConfig.model_validate(
            {
                "column_transformations": column_transformations,
                "endpoint": "https://example.com/api",
                "product_mapping": {},
            }
        )
        assert dag_config.get_expected_columns() == {
            "dest1",
            "dest2",
            "dest3",
            "col",
            "keep",
        }
