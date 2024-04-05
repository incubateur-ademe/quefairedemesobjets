import unittest
import pandas as pd
from dags.utils import mapping_utils


class TestDataTransformations(unittest.TestCase):
    def setUp(self):
        self.df_acteurtype = pd.DataFrame(
            {
                "nom_affiche": [
                    "en ligne (web, mobile)",
                    "artisan, commerce indépendant",
                    "commerce",
                ],
                "id": [1, 2, 3],
            }
        )
        self.df_mapping = pd.DataFrame({"nom": ["donner", "preter"], "id": [1, 2]})
        self.row = {
            "identifiant_externe": "REFASHION_123",
            "service_a_domicile": "service à domicile uniquement",
        }

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
        self.assertEqual(
            mapping_utils.create_identifiant_unique(self.row), "refashion_123_d"
        )

    def test_without_service_a_domicile_only(self):
        self.assertEqual(
            mapping_utils.create_identifiant_unique(self.row), "refashion_123"
        )


if __name__ == "__main__":
    unittest.main()
