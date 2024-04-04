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
                "id": [1, 2, 3, 4],
            }
        )
        self.df_mapping = pd.DataFrame({"nom": ["donner", "preter"], "id": [1, 2]})

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


if __name__ == "__main__":
    unittest.main()
