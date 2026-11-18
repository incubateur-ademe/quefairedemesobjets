from sources.config.airflow_params import EO_NORMALIZATION_RULES
from sources.config.models import (
    CmaSourceAirflowConfig,
    EoSourceAirflowConfig,
    SinoeSourceAirflowConfig,
    SourceConfig,
    config_to_airflow_params,
)


class TestSourceAirflowConfigSubmodels:
    def test_eo_params_exclude_sinoe_only_fields(self):
        config = EoSourceAirflowConfig(endpoint="http://example.com")
        assert config.normalization_rules == EO_NORMALIZATION_RULES
        assert config.product_mapping
        params = config.to_airflow_params()
        assert "dechet_mapping" not in params
        assert "endpoint" in params
        assert "normalization_rules" in params
        assert "product_mapping" in params

    def test_base_hides_source_specific_fields(self):
        params = SourceConfig(
            normalization_rules=[],
            endpoint="http://example.com",
            product_mapping={},
        ).to_airflow_params()
        assert set(params) == {
            "normalization_rules",
            "endpoint",
            "metadata_endpoint",
            "validate_address_with_ban",
            "product_mapping",
            "use_legacy_suggestions",
            "save_datasource_in_warehouse_db",
        }

    def test_sinoe_includes_dechet_mapping(self):
        params = SinoeSourceAirflowConfig(
            normalization_rules=EO_NORMALIZATION_RULES,
            endpoint="http://example.com",
            product_mapping={},
            dechet_mapping={"a": "b"},
        ).to_airflow_params()
        assert "dechet_mapping" in params
        assert params["dechet_mapping"].value == {"a": "b"}

    def test_config_to_airflow_params_alias(self):
        config = EoSourceAirflowConfig(endpoint="http://example.com")
        assert (
            config.to_airflow_params().keys() == config_to_airflow_params(config).keys()
        )

    def test_roundtrip_to_source_config_via_from_airflow_params(self):
        config = CmaSourceAirflowConfig(
            normalization_rules=EO_NORMALIZATION_RULES,
            endpoint="http://example.com",
            product_mapping={"x": "y"},
            ignore_rows_with_null_or_empty_fields=["id"],
        )
        airflow_params = {k: p.value for k, p in config.to_airflow_params().items()}
        parsed = SourceConfig.from_airflow_params(airflow_params)
        assert parsed.endpoint == config.endpoint
        assert parsed.ignore_rows_with_null_or_empty_fields == ["id"]
