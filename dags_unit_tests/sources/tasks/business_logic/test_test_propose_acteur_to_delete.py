from datetime import datetime

import pandas as pd
import pytest
from sources.tasks.business_logic.propose_acteur_to_delete import (
    propose_acteur_to_delete,
)


class TestActeurToDelete:
    @pytest.mark.parametrize(
        (
            "df_acteurs_from_db1, df_acteurs_for_source, df_expected_acteur_to_delete,"
            " expected_metadata"
        ),
        [
            # No deletion
            (
                pd.DataFrame(
                    {
                        "identifiant_unique": ["id1", "id2"],
                        "statut": ["ACTIF", "ACTIF"],
                        "cree_le": [datetime(2024, 1, 1), datetime(2024, 1, 1)],
                        "modifie_le": [datetime(2024, 1, 1), datetime(2024, 1, 1)],
                    }
                ),
                pd.DataFrame(
                    {
                        "identifiant_unique": ["id1", "id2"],
                        "statut": ["ACTIF", "ACTIF"],
                        "cree_le": [datetime(2024, 1, 1), datetime(2024, 1, 1)],
                        "modifie_le": [datetime(2024, 1, 1), datetime(2024, 1, 1)],
                    }
                ),
                pd.DataFrame(
                    columns=[
                        "identifiant_unique",
                        "cree_le",
                        "modifie_le",
                        "statut",
                        "event",
                    ]
                ),
                {"number_of_removed_actors": 0},
            ),
            # No Deletion
            (
                pd.DataFrame(
                    {
                        "identifiant_unique": ["id1", "id2", "id3", "id4"],
                        "statut": ["ACTIF", "ACTIF", "INACTIF", "SUPPRIME"],
                        "cree_le": [
                            datetime(2024, 1, 1),
                            datetime(2024, 1, 1),
                            datetime(2024, 1, 1),
                            datetime(2024, 1, 1),
                        ],
                        "modifie_le": [
                            datetime(2024, 1, 1),
                            datetime(2024, 1, 1),
                            datetime(2024, 1, 1),
                            datetime(2024, 1, 1),
                        ],
                    }
                ),
                pd.DataFrame(
                    {
                        "identifiant_unique": ["id1", "id2"],
                        "statut": ["ACTIF", "ACTIF"],
                        "cree_le": [datetime(2024, 1, 1), datetime(2024, 1, 1)],
                        "modifie_le": [datetime(2024, 1, 1), datetime(2024, 1, 1)],
                    }
                ),
                pd.DataFrame(
                    columns=[
                        "identifiant_unique",
                        "cree_le",
                        "modifie_le",
                        "statut",
                        "event",
                    ]
                ),
                {"number_of_removed_actors": 0},
            ),
            # Deletion
            (
                pd.DataFrame(
                    {
                        "identifiant_unique": ["id1", "id2"],
                        "statut": ["ACTIF", "ACTIF"],
                        "cree_le": [datetime(2024, 1, 1), datetime(2024, 1, 1)],
                        "modifie_le": [datetime(2024, 1, 1), datetime(2024, 1, 1)],
                    }
                ),
                pd.DataFrame(
                    {
                        "identifiant_unique": ["id1"],
                        "statut": ["ACTIF"],
                        "cree_le": [datetime(2024, 1, 1)],
                        "modifie_le": [datetime(2024, 1, 1)],
                    }
                ),
                pd.DataFrame(
                    {
                        "identifiant_unique": ["id2"],
                        "cree_le": [datetime(2024, 1, 1)],
                        "modifie_le": [datetime(2024, 1, 1)],
                        "statut": ["SUPPRIME"],
                        "event": ["UPDATE_ACTOR"],
                    }
                ),
                {"number_of_removed_actors": 1},
            ),
        ],
    )
    def test_propose_acteur_to_delete(
        self,
        df_acteurs_from_db1,
        df_acteurs_for_source,
        df_expected_acteur_to_delete,
        expected_metadata,
    ):
        result = propose_acteur_to_delete(
            df_acteurs_for_source=df_acteurs_for_source,
            df_acteurs_from_db=df_acteurs_from_db1,
        )
        df_returned_acteur_to_delete = result["df_acteur_to_delete"]

        pd.testing.assert_frame_equal(
            df_returned_acteur_to_delete.reset_index(drop=True),
            df_expected_acteur_to_delete.reset_index(drop=True),
            check_dtype=False,
        )
        assert result["metadata"] == expected_metadata
