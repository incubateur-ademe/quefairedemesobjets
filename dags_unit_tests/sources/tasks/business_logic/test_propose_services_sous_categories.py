import pandas as pd
import pytest
from sources.tasks.business_logic.propose_services_sous_categories import (
    propose_services_sous_categories,
)


class TestProposeServicesSousCategories:
    def test_create_proposition_services_sous_categories(
        self, souscategorieobjet_code_by_id
    ):
        df_result = propose_services_sous_categories(
            df_ps=pd.DataFrame(
                {
                    "action_id": [1, 3, 1, 3],
                    "acteur_id": [1, 1, 2, 2],
                    "action": ["reparer", "trier", "reparer", "trier"],
                    "sous_categories": [
                        ["smartphone, tablette et console"],
                        ["smartphone, tablette et console"],
                        ["ecran"],
                        ["ecran"],
                    ],
                    "id": [1, 2, 3, 4],
                }
            ),
            souscats_id_by_code=souscategorieobjet_code_by_id,
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

    def test_create_proposition_services_sous_categories_empty_products(
        self, souscategorieobjet_code_by_id
    ):
        with pytest.raises(ValueError):
            propose_services_sous_categories(
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
            )
