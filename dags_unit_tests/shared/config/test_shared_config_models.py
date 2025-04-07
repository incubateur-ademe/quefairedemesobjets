from typing import Optional

import pytest
from pydantic import BaseModel, Field

from dags.shared.config.models import config_to_airflow_params


class MyModel(BaseModel):
    dry_run: bool = Field(
        default=True,
        description="🚱 Si coché...",
    )
    some_string: str = Field(
        default="foo",
        description="SOME STRING",
    )
    opt_string_untouched: Optional[str] = Field(
        default=None,
        description="OPT STRING UNTOUCHED",
    )
    opt_string_changed: Optional[str] = Field(
        default=None,
        description="OPT STRING CHANGED",
    )


class TestConfigModelToAirflowParams:
    @pytest.fixture
    def model_instance(self):
        return MyModel(opt_string_changed="bar")

    @pytest.fixture
    def params(self, model_instance):
        return config_to_airflow_params(model_instance)

    def test_boolean(self, params):
        param = params["dry_run"]
        assert param.value is True
        assert param.schema["type"] == "boolean"
        assert param.schema["description_md"] == "🚱 Si coché..."

    def test_string(self, params):
        param = params["some_string"]
        assert param.value == "foo"
        assert param.schema["type"] == "string"

    def test_opt_string_untouched(self, params):
        param = params["opt_string_untouched"]
        assert param.value is None
        assert param.schema["type"] == ["null", "string"]

    def test_opt_string_changed(self, params):
        param = params["opt_string_changed"]
        assert param.value == "bar"
        assert param.schema["type"] == ["null", "string"]
