from datetime import datetime

import pandas as pd
import pytest
from sources.tasks.business_logic.serialize_to_json import db_data_prepare


class TestSerializeToJson:

    @pytest.mark.parametrize(
        "propose_labels, expected_labels",
        [
            (
                pd.DataFrame(columns=["acteur_id", "labelqualite_id"]),
                {0: None, 1: None},
            ),
            (
                pd.DataFrame(
                    {
                        "acteur_id": [1, 2, 2],
                        "labelqualite_id": [1, 1, 2],
                    }
                ),
                {
                    0: [
                        {
                            "acteur_id": 1,
                            "labelqualite_id": 1,
                        }
                    ],
                    1: [
                        {
                            "acteur_id": 2,
                            "labelqualite_id": 1,
                        },
                        {
                            "acteur_id": 2,
                            "labelqualite_id": 2,
                        },
                    ],
                },
            ),
        ],
    )
    def test_serialize_to_json_labels(
        self,
        df_ps,
        df_ps_sscat,
        propose_labels,
        expected_labels,
    ):

        df_result = db_data_prepare(
            df_acteur_to_delete=pd.DataFrame(
                {
                    "identifiant_unique": [3],
                    "statut": ["ACTIF"],
                    "cree_le": [datetime(2024, 1, 1)],
                }
            ),
            df_actors=pd.DataFrame({"identifiant_unique": [1, 2]}),
            df_ps=df_ps,
            df_ps_sscat=df_ps_sscat,
            df_labels=propose_labels,
            df_acteur_services=pd.DataFrame(
                columns=["acteur_id", "acteurservice_id", "acteurservice"]
            ),
        )
        result = df_result["all"]["df"].to_dict()
        labels = result["labels"]

        assert labels == expected_labels

    @pytest.mark.parametrize(
        "propose_acteur_services, expected_acteur_services",
        [
            (
                pd.DataFrame(
                    columns=["acteur_id", "acteurservice_id", "acteurservice"]
                ),
                {0: None, 1: None},
            ),
            (
                pd.DataFrame(
                    {
                        "acteur_id": [1, 2, 2],
                        "acteurservice_id": [10, 10, 20],
                        "acteurservice": [
                            "Service de réparation",
                            "Service de réparation",
                            "Collecte par une structure spécialisée",
                        ],
                    }
                ),
                {
                    0: [
                        {
                            "acteur_id": 1,
                            "acteurservice": "Service de réparation",
                            "acteurservice_id": 10,
                        }
                    ],
                    1: [
                        {
                            "acteur_id": 2,
                            "acteurservice": "Service de réparation",
                            "acteurservice_id": 10,
                        },
                        {
                            "acteur_id": 2,
                            "acteurservice": "Collecte par une structure spécialisée",
                            "acteurservice_id": 20,
                        },
                    ],
                },
            ),
        ],
    )
    def test_serialize_to_json_acteur_services(
        self,
        df_ps,
        df_ps_sscat,
        propose_acteur_services,
        expected_acteur_services,
    ):
        df_result = db_data_prepare(
            df_acteur_to_delete=pd.DataFrame(
                {
                    "identifiant_unique": [3],
                    "statut": ["ACTIF"],
                    "cree_le": [datetime(2024, 1, 1)],
                }
            ),
            df_actors=pd.DataFrame({"identifiant_unique": [1, 2]}),
            df_ps=df_ps,
            df_ps_sscat=df_ps_sscat,
            df_labels=pd.DataFrame(columns=["acteur_id", "labelqualite_id"]),
            df_acteur_services=propose_acteur_services,
        )
        result = df_result["all"]["df"].to_dict()
        acteur_services = result["acteur_services"]

        assert acteur_services == expected_acteur_services
