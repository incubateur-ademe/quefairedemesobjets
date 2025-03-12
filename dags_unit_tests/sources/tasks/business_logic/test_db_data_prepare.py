import pandas as pd
import pytest

from dags.sources.tasks.business_logic.db_data_prepare import db_data_prepare


@pytest.mark.parametrize(
    "df_acteur,df_acteur_from_db, expected_output",
    [
        (
            pd.DataFrame(
                {
                    "identifiant_unique": ["2", "3"],
                    "statut": ["ACTIF", "ACTIF"],
                    "cree_le": ["2021-01-01", "2021-01-01"],
                    "proposition_service_codes": [
                        [{"prop2": "val2"}],
                        [{"prop3": "val3"}],
                    ],
                }
            ),
            pd.DataFrame(
                {
                    "identifiant_unique": ["1", "2"],
                    "statut": ["ACTIF", "ACTIF"],
                    "cree_le": ["2021-01-01", "2021-01-01"],
                }
            ),
            {
                "df_acteur_to_create": pd.DataFrame(
                    {
                        "identifiant_unique": ["3"],
                        "statut": ["ACTIF"],
                        "cree_le": ["2021-01-01"],
                        "proposition_service_codes": [[{"prop3": "val3"}]],
                        "suggestion": [
                            '{"identifiant_unique": "3", "statut": "ACTIF",'
                            ' "cree_le": "2021-01-01",'
                            ' "proposition_service_codes": [{"prop3": "val3"}]}'
                        ],
                        "contexte": None,
                    }
                ),
                "df_acteur_to_update": pd.DataFrame(
                    {
                        "identifiant_unique": ["2"],
                        "statut": ["ACTIF"],
                        "cree_le": ["2021-01-01"],
                        "proposition_service_codes": [[{"prop2": "val2"}]],
                        "suggestion": [
                            '{"identifiant_unique": "2", "statut": "ACTIF",'
                            ' "cree_le": "2021-01-01",'
                            ' "proposition_service_codes": [{"prop2": "val2"}]}'
                        ],
                        "contexte": [
                            '{"identifiant_unique": "2", "statut": "ACTIF",'
                            ' "cree_le": "2021-01-01"}'
                        ],
                    }
                ),
                "df_acteur_to_delete": pd.DataFrame(
                    {
                        "identifiant_unique": ["1"],
                        "statut": ["SUPPRIME"],
                        "suggestion": [
                            '{"identifiant_unique": "1", "statut": "SUPPRIME"}'
                        ],
                        "contexte": [
                            '{"identifiant_unique": "1", "statut": "ACTIF",'
                            ' "cree_le": "2021-01-01"}'
                        ],
                    }
                ),
            },
        )
    ],
)
def test_db_data_prepare(df_acteur, df_acteur_from_db, expected_output):
    result = db_data_prepare(df_acteur, df_acteur_from_db)

    pd.testing.assert_frame_equal(
        result["df_acteur_to_delete"].reset_index(drop=True),
        expected_output["df_acteur_to_delete"].reset_index(drop=True),
    )
    pd.testing.assert_frame_equal(
        result["df_acteur_to_create"].reset_index(drop=True),
        expected_output["df_acteur_to_create"].reset_index(drop=True),
    )
    pd.testing.assert_frame_equal(
        result["df_acteur_to_update"].reset_index(drop=True),
        expected_output["df_acteur_to_update"].reset_index(drop=True),
    )
