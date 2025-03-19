import pytest

from dags.utils.dbt import dbt_assert_model_schema

MODEL_NAME_OK = "marts_enrich_ae_rgpd"
COLUMNS_OK = ["siren", "acteur_id"]


class TestDbtCheckModelSchema:

    def test_working(self):
        dbt_assert_model_schema(MODEL_NAME_OK, COLUMNS_OK)
        pass

    def test_raise_if_column_not_found(self):
        with pytest.raises(ValueError):
            dbt_assert_model_schema(
                MODEL_NAME_OK, ["siren", "🔴 COLUMN DOES NOT EXIST"]
            )

    def test_raise_if_model_not_found(self):
        with pytest.raises(ValueError):
            dbt_assert_model_schema("🔴 MODEL DOES NOT EXIST", COLUMNS_OK)
