import pytest
from sources.tasks.business_logic.source_config_validate import source_config_validate


@pytest.fixture
def valid_params():
    return {
        "product_mapping": {
            "product1": ["code1", "code2"],
            "product2": "code3",
            "product3": [],
        },
        "column_mapping": {
            "col1": "mapped_col1",
            "col2": "mapped_col2",
        },
        "column_transformations": [
            (
                '{"origin": "src", "transformation": "convert_opening_hours",'
                ' "destination": "dest"}'
            )
        ],
    }


@pytest.fixture
def codes_sc_db():
    return {"code1", "code2", "code3"}


def test_source_config_validate_valid(valid_params, codes_sc_db):
    assert source_config_validate(params=valid_params, codes_sc_db=codes_sc_db) is None


def test_missing_product_mapping(valid_params, codes_sc_db):
    params = valid_params.copy()
    del params["product_mapping"]
    with pytest.raises(ValueError):
        source_config_validate(params=params, codes_sc_db=codes_sc_db)


# TODO : Pourquoi la levé d'exception est commentée ?
# def test_product_mapping_no_code(valid_params, codes_sc_db):
#     params = valid_params.copy()
#     params["product_mapping"]["product3"] = ["code4"]
#     with pytest.raises(ValueError):
#         source_config_validate(params=params, codes_sc_db=codes_sc_db)


def test_column_mapping_not_dict(valid_params, codes_sc_db):
    params = valid_params.copy()
    params["column_mapping"] = "not_a_dict"
    with pytest.raises(ValueError):
        source_config_validate(params=params, codes_sc_db=codes_sc_db)


def test_column_transformations_not_list(valid_params, codes_sc_db):
    params = valid_params.copy()
    params["column_transformations"] = "not_a_list"
    with pytest.raises(ValueError):
        source_config_validate(params=params, codes_sc_db=codes_sc_db)


def test_column_transformations_invalid_function(valid_params, codes_sc_db):
    params = valid_params.copy()
    params["column_transformations"] = [
        '{"origin": "src", "transformation": "invalid_function", "destination": "dest"}'
    ]
    with pytest.raises(ValueError):
        source_config_validate(params=params, codes_sc_db=codes_sc_db)
