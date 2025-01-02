import pandas as pd
import pytest
from utils import mapping_utils


@pytest.fixture
def acteurtype_id_by_code():
    return {
        "acteur_digital": 1,
        "artisan": 2,
        "commerce": 3,
    }


@pytest.fixture
def df_mapping():
    return pd.DataFrame({"code": ["donner", "preter"], "id": [1, 2]})


class TestDataTransformations:

    def test_transform_acteur_type_id(self, acteurtype_id_by_code):
        value = "Solution en ligne (site web, app. mobile)"
        expected_id = 1
        result_id = mapping_utils.transform_acteur_type_id(value, acteurtype_id_by_code)
        assert result_id == expected_id

    def test_get_id_from_code(self, df_mapping):
        value = "donner"
        expected_id = 1
        result_id = mapping_utils.get_id_from_code(value, df_mapping)
        assert result_id == expected_id

    # def test_with_service_a_domicile_only(self):
    #     row = {
    #         "source_code": "ECOORG",
    #         "identifiant_externe": "123AbC",
    #         "type_de_point_de_collecte": "Solution en ligne (site web, app. mobile)",
    #     }
    #     assert mapping_utils.create_identifiant_unique(row) == "ecoorg_123AbC_d"

    # def test_without_service_a_domicile_only(self):
    #     row = {
    #         "source_code": "ECOORG",
    #         "identifiant_externe": "123AbC",
    #         "type_de_point_de_collecte": "Artisan, commerce indépendant ",
    #     }
    #     assert mapping_utils.create_identifiant_unique(row), "ecoorg_123AbC"


class TestTransformFloat:
    def test_float(self):
        assert mapping_utils.transform_float(1.0) == 1.0

    def test_string(self):
        assert mapping_utils.transform_float("1,0") == 1.0
        assert mapping_utils.transform_float("1.0") == 1.0

    def test_invalid_string(self):
        assert not mapping_utils.transform_float("1.0.0")
        assert not mapping_utils.transform_float("NaN")

    def test_invalid_type(self):
        assert not mapping_utils.transform_float(None)
