import pandas as pd
import pytest
from sources.tasks.business_logic.propose_ps import propose_ps


@pytest.fixture
def actions_id_by_code():
    return {"reparer": 1, "donner": 2, "trier": 3}


class TestCreatePropositionService:

    def test_create_ps_empty(
        self,
        actions_id_by_code,
    ):
        df_create_actors = pd.DataFrame(
            {
                "identifiant_unique": [1],
                "produitsdechets_acceptes": ["téléphones portables"],
                "point_dapport_de_service_reparation": [False],
                "point_dapport_pour_reemploi": [False],
                "point_de_reparation": [False],
                "point_de_collecte_ou_de_reprise_des_dechets": [False],
            }
        )

        with pytest.raises(ValueError):
            propose_ps(
                df=df_create_actors,
                dps_max_id=1,
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
                        "produitsdechets_acceptes": ["téléphones portables"],
                        "point_dapport_de_service_reparation": [True],
                        "point_dapport_pour_reemploi": [False],
                        "point_de_reparation": [False],
                        "point_de_collecte_ou_de_reprise_des_dechets": [False],
                    }
                ),
                pd.DataFrame(
                    {
                        "action_id": [1],
                        "acteur_id": [1],
                        "action": ["reparer"],
                        "sous_categories": ["téléphones portables"],
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
                        "produitsdechets_acceptes": ["téléphones portables"],
                        "point_dapport_de_service_reparation": [False],
                        "point_dapport_pour_reemploi": [True],
                        "point_de_reparation": [False],
                        "point_de_collecte_ou_de_reprise_des_dechets": [False],
                    }
                ),
                pd.DataFrame(
                    {
                        "action_id": [2],
                        "acteur_id": [1],
                        "action": ["donner"],
                        "sous_categories": ["téléphones portables"],
                        "id": [1],
                    },
                ),
                {"number_of_merged_actors": 0, "number_of_propositionservices": 1},
            ),
            # Point Réparation
            (
                pd.DataFrame(
                    {
                        "identifiant_unique": [1],
                        "produitsdechets_acceptes": ["téléphones portables"],
                        "point_dapport_de_service_reparation": [False],
                        "point_dapport_pour_reemploi": [False],
                        "point_de_reparation": [True],
                        "point_de_collecte_ou_de_reprise_des_dechets": [False],
                    }
                ),
                pd.DataFrame(
                    {
                        "action_id": [1],
                        "acteur_id": [1],
                        "action": ["reparer"],
                        "sous_categories": ["téléphones portables"],
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
                        "produitsdechets_acceptes": ["téléphones portables"],
                        "point_dapport_de_service_reparation": [False],
                        "point_dapport_pour_reemploi": [False],
                        "point_de_reparation": [False],
                        "point_de_collecte_ou_de_reprise_des_dechets": [True],
                    }
                ),
                pd.DataFrame(
                    {
                        "action_id": [3],
                        "acteur_id": [1],
                        "action": ["trier"],
                        "sous_categories": ["téléphones portables"],
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
                        "produitsdechets_acceptes": ["téléphones portables"],
                        "point_dapport_de_service_reparation": [True],
                        "point_dapport_pour_reemploi": [True],
                        "point_de_reparation": [True],
                        "point_de_collecte_ou_de_reprise_des_dechets": [True],
                    }
                ),
                pd.DataFrame(
                    {
                        "action_id": [1, 2, 3],
                        "acteur_id": [1, 1, 1],
                        "action": ["reparer", "donner", "trier"],
                        "sous_categories": [
                            "téléphones portables",
                            "téléphones portables",
                            "téléphones portables",
                        ],
                        "id": [1, 2, 3],
                    },
                ),
                {"number_of_merged_actors": 0, "number_of_propositionservices": 3},
            ),
        ],
    )
    def test_create_ps_services(
        self,
        df_create_actors,
        expected_df,
        expected_metadata,
        actions_id_by_code,
    ):
        result = propose_ps(
            df=df_create_actors,
            dps_max_id=1,
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
                "produitsdechets_acceptes": [
                    "téléphones portables",
                    "téléphones portables",
                ],
                "point_dapport_de_service_reparation": [False, False],
                "point_dapport_pour_reemploi": [False, False],
                "point_de_reparation": [False, False],
                "point_de_collecte_ou_de_reprise_des_dechets": [True, True],
            }
        )

        expected_df = pd.DataFrame(
            {
                "action_id": [3, 3],
                "acteur_id": [1, 2],
                "action": ["trier", "trier"],
                "sous_categories": ["téléphones portables", "téléphones portables"],
                "id": [1, 2],
            }
        )
        expected_metadata = {
            "number_of_merged_actors": 0,
            "number_of_propositionservices": 2,
        }

        result = propose_ps(
            df=df_create_actors,
            dps_max_id=1,
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
                "identifiant_unique": [1, 1],
                "produitsdechets_acceptes": [
                    "téléphones portables",
                    "écrans",
                ],
                "point_dapport_de_service_reparation": [True, False],
                "point_dapport_pour_reemploi": [False, False],
                "point_de_reparation": [False, True],
                "point_de_collecte_ou_de_reprise_des_dechets": [False, False],
            }
        )

        df_expected = pd.DataFrame(
            {
                "action_id": [1],
                "acteur_id": [1],
                "action": ["reparer"],
                "sous_categories": ["téléphones portables | écrans"],
                "id": [1],
            }
        )
        expected_metadata = {
            "number_of_merged_actors": 0,
            "number_of_propositionservices": 1,
        }

        result = propose_ps(
            df=df_create_actors,
            dps_max_id=1,
            actions_id_by_code=actions_id_by_code,
        )

        assert result["df"].equals(df_expected)
        assert result["metadata"] == expected_metadata
