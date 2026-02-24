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
    result = db_data_prepare(
        df_acteur=df_acteur,
        df_acteur_from_db=df_acteur_from_db,
    )

    # Vérifier que les DataFrames sont retournés
    assert "df_acteur_to_create" in result
    assert "df_acteur_to_update" in result
    assert "df_acteur_to_delete" in result

    # Vérifier les DataFrames avec pd.testing.assert_frame_equal
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

    # Vérifier les métadonnées
    assert result["metadata_to_create"]["Nombre d'acteurs à créer"] == len(
        expected_output["df_acteur_to_create"]
    )
    assert result["metadata_to_update"]["Nombre d'acteurs à mettre à jour"] == len(
        expected_output["df_acteur_to_update"]
    )
    assert result["metadata_to_delete"]["Nombre d'acteurs à supprimer"] == len(
        expected_output["df_acteur_to_delete"]
    )
