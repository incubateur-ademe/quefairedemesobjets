import pytest
from sources.tasks.airflow_logic.config_management import NormalizationColumnTransform
from sources.tasks.business_logic.source_config_validate import source_config_validate


@pytest.fixture
def valid_params():
    return {
        "product_mapping": {
            "product1": ["code1", "code2"],
            "product2": "code3",
            "product3": [],
        },
        "normalization_rules": [],
        "endpoint": "https://api.example.com",
    }


@pytest.fixture
def codes_sc_db():
    return {"code1", "code2", "code3"}


def test_source_config_validate_valid(codes_sc_db, dag_config):
    dag_config.product_mapping = {
        "product1": ["code1", "code2"],
        "product2": "code3",
    }
    assert (
        source_config_validate(dag_config=dag_config, codes_sc_db=codes_sc_db) is None
    )


def test_mandatory_columns(codes_sc_db, dag_config):
    dag_config.normalization_rules = []
    with pytest.raises(ValueError) as error:
        source_config_validate(dag_config=dag_config, codes_sc_db=codes_sc_db)
    assert "Mandatory columns are missing in dag_config" in str(error)


def test_product_mapping_no_code(codes_sc_db, dag_config):
    dag_config.product_mapping["product3"] = ["code4"]
    with pytest.raises(ValueError) as error:
        source_config_validate(dag_config=dag_config, codes_sc_db=codes_sc_db)
    assert "Codes product_mapping invalides:" in str(error)


def test_product_mapping_missing(codes_sc_db, dag_config):
    dag_config.product_mapping = {}
    with pytest.raises(ValueError) as error:
        source_config_validate(dag_config=dag_config, codes_sc_db=codes_sc_db)
    assert "product_mapping manquant pour la source" in str(error)


def test_normalization_rules_invalid_function(codes_sc_db, dag_config):
    dag_config.normalization_rules.append(
        NormalizationColumnTransform(
            origin="src", transformation="invalid_function", destination="dest"
        )
    )
    with pytest.raises(ValueError) as error:
        source_config_validate(dag_config=dag_config, codes_sc_db=codes_sc_db)
    assert "La fonction de transformation invalid_function n'existe pas" in str(error)
