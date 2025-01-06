import pandas as pd
import pytest
from sources.tasks.business_logic.propose_services import propose_services


@pytest.fixture
def actions_id_by_code():
    return {"reparer": 1, "donner": 2, "trier": 3}


class TestCreatePropositionService:

    def test_create_proposition_services_empty(
        self,
        actions_id_by_code,
    ):
        df_create_actors = pd.DataFrame(
            {
                "identifiant_unique": [1],
                "souscategorie_codes": [["smartphone, tablette et console"]],
                "action_codes": [[]],
            }
        )

        with pytest.raises(ValueError):
            propose_services(
                df=df_create_actors,
                displayedpropositionservice_max_id=1,
                actions_id_by_code=actions_id_by_code,
            )

    @pytest.mark.parametrize(
        "df_create_actors, expected_df, expected_metadata",
        [
            # Service Réparation
            (
                pd.DataFrame(
                    {
                        "identifiant_unique": [1],
                        "souscategorie_codes": [["smartphone, tablette et console"]],
                        "action_codes": [["reparer"]],
                    }
                ),
                pd.DataFrame(
                    {
                        "action_id": [1],
                        "acteur_id": [1],
                        "action": ["reparer"],
                        "sous_categories": [["smartphone, tablette et console"]],
                        "id": [1],
                    },
                ),
                {"number_of_merged_actors": 0, "number_of_propositionservices": 1},
            ),
            # Service Réemploi
            (
                pd.DataFrame(
                    {
                        "identifiant_unique": [1],
                        "souscategorie_codes": [["smartphone, tablette et console"]],
                        "action_codes": [["donner"]],
                    }
                ),
                pd.DataFrame(
                    {
                        "action_id": [2],
                        "acteur_id": [1],
                        "action": ["donner"],
                        "sous_categories": [["smartphone, tablette et console"]],
                        "id": [1],
                    },
                ),
                {"number_of_merged_actors": 0, "number_of_propositionservices": 1},
            ),
            # Point Collecte (tri)
            (
                pd.DataFrame(
                    {
                        "identifiant_unique": [1],
                        "souscategorie_codes": [["smartphone, tablette et console"]],
                        "action_codes": [["trier"]],
                    }
                ),
                pd.DataFrame(
                    {
                        "action_id": [3],
                        "acteur_id": [1],
                        "action": ["trier"],
                        "sous_categories": [["smartphone, tablette et console"]],
                        "id": [1],
                    },
                ),
                {"number_of_merged_actors": 0, "number_of_propositionservices": 1},
            ),
            # All services
            (
                pd.DataFrame(
                    {
                        "identifiant_unique": [1],
                        "souscategorie_codes": [["smartphone, tablette et console"]],
                        "action_codes": [["reparer", "donner", "trier"]],
                    }
                ),
                pd.DataFrame(
                    {
                        "action_id": [1, 2, 3],
                        "acteur_id": [1, 1, 1],
                        "action": ["reparer", "donner", "trier"],
                        "sous_categories": [
                            ["smartphone, tablette et console"],
                            ["smartphone, tablette et console"],
                            ["smartphone, tablette et console"],
                        ],
                        "id": [1, 2, 3],
                    },
                ),
                {"number_of_merged_actors": 0, "number_of_propositionservices": 3},
            ),
        ],
    )
    def test_create_proposition_services_services(
        self,
        df_create_actors,
        expected_df,
        expected_metadata,
        actions_id_by_code,
    ):
        result = propose_services(
            df=df_create_actors,
            displayedpropositionservice_max_id=1,
            actions_id_by_code=actions_id_by_code,
        )

        assert result["df"].equals(expected_df)
        assert result["metadata"] == expected_metadata

    def test_create_proposition_multiple_actor(
        self,
        actions_id_by_code,
    ):
        df_create_actors = pd.DataFrame(
            {
                "identifiant_unique": [1, 2],
                "souscategorie_codes": [
                    "smartphone, tablette et console",
                    "smartphone, tablette et console",
                ],
                "action_codes": [["trier"], ["trier"]],
            }
        )

        expected_df = pd.DataFrame(
            {
                "action_id": [3, 3],
                "acteur_id": [1, 2],
                "action": ["trier", "trier"],
                "sous_categories": [
                    "smartphone, tablette et console",
                    "smartphone, tablette et console",
                ],
                "id": [1, 2],
            }
        )
        expected_metadata = {
            "number_of_merged_actors": 0,
            "number_of_propositionservices": 2,
        }

        result = propose_services(
            df=df_create_actors,
            displayedpropositionservice_max_id=1,
            actions_id_by_code=actions_id_by_code,
        )

        assert result["df"].equals(expected_df)
        assert result["metadata"] == expected_metadata

    def test_create_proposition_multiple_product(
        self,
        actions_id_by_code,
    ):
        df_create_actors = pd.DataFrame(
            {
                "identifiant_unique": [1],
                "action_codes": [["reparer"]],
                "souscategorie_codes": [["smartphone, tablette et console", "ecran"]],
            }
        )

        df_expected = pd.DataFrame(
            {
                "action_id": [1],
                "acteur_id": [1],
                "action": ["reparer"],
                "sous_categories": [["smartphone, tablette et console", "ecran"]],
                "id": [1],
            }
        )
        expected_metadata = {
            "number_of_merged_actors": 0,
            "number_of_propositionservices": 1,
        }

        result = propose_services(
            df=df_create_actors,
            displayedpropositionservice_max_id=1,
            actions_id_by_code=actions_id_by_code,
        )

        assert result["df"].equals(df_expected)
        assert result["metadata"] == expected_metadata
