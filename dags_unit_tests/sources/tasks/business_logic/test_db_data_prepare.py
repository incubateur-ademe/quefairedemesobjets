import pandas as pd
import pytest

from dags.sources.tasks.business_logic.db_data_prepare import db_data_prepare


@pytest.mark.parametrize(
    "df_acteur,df_acteur_from_db, expected_output",
    [
        (
            pd.DataFrame(
                {
                    "id": ["2", "3"],
                    "statut": ["ACTIF", "ACTIF"],
                    "cree_le": ["2021-01-01", "2021-01-01"],
                    "proposition_services": [[{"prop2": "val2"}], [{"prop3": "val3"}]],
                }
            ),
            pd.DataFrame(
                {
                    "id": ["1", "2"],
                    "statut": ["ACTIF", "ACTIF"],
                    "cree_le": ["2021-01-01", "2021-01-01"],
                }
            ),
            {
                "df_acteur_to_create": pd.DataFrame(
                    {
                        "id": ["3"],
                        "statut": ["ACTIF"],
                        "cree_le": ["2021-01-01"],
                        "proposition_services": [[{"prop3": "val3"}]],
                        "suggestion": [
                            '{"id": "3", "statut": "ACTIF",'
                            ' "cree_le": "2021-01-01",'
                            ' "proposition_services": [{"prop3": "val3"}]}'
                        ],
                        "contexte": None,
                    }
                ),
                "df_acteur_to_update": pd.DataFrame(
                    {
                        "id": ["2"],
                        "statut": ["ACTIF"],
                        "cree_le": ["2021-01-01"],
                        "proposition_services": [[{"prop2": "val2"}]],
                        "suggestion": [
                            '{"id": "2", "statut": "ACTIF",'
                            ' "cree_le": "2021-01-01",'
                            ' "proposition_services": [{"prop2": "val2"}]}'
                        ],
                        "contexte": [
                            '{"id": "2", "statut": "ACTIF",' ' "cree_le": "2021-01-01"}'
                        ],
                    }
                ),
                "df_acteur_to_delete": pd.DataFrame(
                    {
                        "id": ["1"],
                        "statut": ["SUPPRIME"],
                        "suggestion": ['{"id": "1", "statut": "SUPPRIME"}'],
                        "contexte": [
                            '{"id": "1", "statut": "ACTIF",' ' "cree_le": "2021-01-01"}'
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
