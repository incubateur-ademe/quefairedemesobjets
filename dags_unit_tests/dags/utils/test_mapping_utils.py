import unittest

import numpy as np
import pandas as pd
from utils import mapping_utils


class TestDataTransformations(unittest.TestCase):
    def setUp(self):
        self.df_acteurtype = pd.DataFrame(
            {
                "code": [
                    "acteur_digital",
                    "artisan",
                    "commerce",
                ],
                "id": [1, 2, 3],
            }
        )
        self.df_mapping = pd.DataFrame({"code": ["donner", "preter"], "id": [1, 2]})

    def test_transform_acteur_type_id(self):
        value = "Solution en ligne (site web, app. mobile)"
        expected_id = 1
        result_id = mapping_utils.transform_acteur_type_id(value, self.df_acteurtype)
        self.assertEqual(result_id, expected_id)

    def test_get_id_from_code(self):
        value = "donner"
        expected_id = 1
        result_id = mapping_utils.get_id_from_code(value, self.df_mapping)
        self.assertEqual(result_id, expected_id)

    def test_with_service_a_domicile_only(self):
        row = {
            "ecoorganisme": "ECOORG",
            "identifiant_externe": "123AbC",
            "type_de_point_de_collecte": "Solution en ligne (site web, app. mobile)",
        }
        self.assertEqual(
            mapping_utils.create_identifiant_unique(row), "ecoorg_123AbC_d"
        )

    def test_without_service_a_domicile_only(self):
        row = {
            "ecoorganisme": "ECOORG",
            "identifiant_externe": "123AbC",
            "type_de_point_de_collecte": "Artisan, commerce indépendant ",
        }
        self.assertEqual(mapping_utils.create_identifiant_unique(row), "ecoorg_123AbC")

    def test_process_siret_value(self):
        self.assertEqual(mapping_utils.process_siret("123456789012345"), None)
        self.assertEqual(mapping_utils.process_siret(np.nan), None)
        self.assertEqual(
            mapping_utils.process_siret("98765432109876"), "98765432109876"
        )
        self.assertEqual(mapping_utils.process_siret("8765432109876"), "08765432109876")

    def test_process_telephone_value(self):
        self.assertEqual(
            mapping_utils.process_phone_number("33 1 23 45 67 89"), "0123456789"
        )
        self.assertEqual(mapping_utils.process_phone_number("0612345678"), "0612345678")
        self.assertEqual(mapping_utils.process_phone_number(None), None)
        self.assertEqual(
            mapping_utils.process_phone_number("+33612345678"), "+33612345678"
        )


class TestTransformFloat(unittest.TestCase):
    def test_float(self):
        self.assertEqual(mapping_utils.transform_float(1.0), 1.0)

    def test_string(self):
        self.assertEqual(mapping_utils.transform_float("1,0"), 1.0)
        self.assertEqual(mapping_utils.transform_float("1.0"), 1.0)

    def test_invalid_string(self):
        self.assertIsNone(mapping_utils.transform_float("1.0.0"))
        self.assertIsNone(mapping_utils.transform_float("NaN"))

    def test_invalid_type(self):
        self.assertIsNone(mapping_utils.transform_float(None))


if __name__ == "__main__":
    unittest.main()
