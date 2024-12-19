import pandas as pd
import pytest
from sources.tasks.business_logic.propose_ps_sscat import propose_ps_sscat


class TestProposeServicesSousCategories:
    def test_create_ps_sscat(self, souscategorieobjet_code_by_id):
        df_result = propose_ps_sscat(
            df_ps=pd.DataFrame(
                {
                    "action_id": [1, 3, 1, 3],
                    "acteur_id": [1, 1, 2, 2],
                    "action": ["reparer", "trier", "reparer", "trier"],
                    "acteur_service": [
                        "Service de réparation",
                        "Collecte par une structure spécialisée",
                        "Service de réparation",
                        "Collecte par une structure spécialisée",
                    ],
                    "sous_categories": [
                        "téléphones portables",
                        "téléphones portables",
                        "ecrans",
                        "ecrans",
                    ],
                    "id": [1, 2, 3, 4],
                }
            ),
            souscats_id_by_code=souscategorieobjet_code_by_id,
            product_mapping={
                "téléphones portables": "smartphone, tablette et console",
                "ecrans": "ecran",
            },
        )

        pd.testing.assert_frame_equal(
            df_result,
            pd.DataFrame(
                {
                    "propositionservice_id": [1, 2, 3, 4],
                    "souscategorieobjet_id": [102, 102, 101, 101],
                    "souscategorie": [
                        "smartphone, tablette et console",
                        "smartphone, tablette et console",
                        "ecran",
                        "ecran",
                    ],
                }
            ),
        )

    def test_create_ps_sscat_empty_products(self, souscategorieobjet_code_by_id):
        with pytest.raises(ValueError):
            propose_ps_sscat(
                df_ps=pd.DataFrame(
                    {
                        "action_id": [1, 1],
                        "acteur_id": [1, 2],
                        "action": ["reparer", "reparer"],
                        "acteur_service": [
                            "Service de réparation",
                            "Service de réparation",
                        ],
                        "sous_categories": ["", []],
                        "id": [1, 2],
                    }
                ),
                souscats_id_by_code=souscategorieobjet_code_by_id,
                product_mapping={},
            )
