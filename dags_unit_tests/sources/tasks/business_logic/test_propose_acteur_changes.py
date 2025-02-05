from datetime import datetime

import pandas as pd
import pytest
from sources.tasks.business_logic.propose_acteur_changes import propose_acteur_changes


class TestProposeActeurChangesCreeLe:
    @pytest.mark.parametrize(
        "df_acteur, df_data_from_api, expected_cree_le",
        [
            # Empty acteur
            (
                pd.DataFrame(
                    columns=[
                        "id",
                        "source_id",
                        "statut",
                        "cree_le",
                        "modifie_le",
                    ]
                ),
                pd.DataFrame(
                    {
                        "id": ["source1_id1"],
                        "produitsdechets_acceptes": ["12345678"],
                        "nom_de_lorganisme": ["Eco1"],
                        "ecoorganisme": ["source1"],
                    }
                ),
                datetime.now().date(),
            ),
            (
                pd.DataFrame(
                    {
                        "id": ["source1_id1"],
                        "source_id": [101],
                        "statut": ["ACTIF"],
                        "cree_le": [datetime(2024, 1, 1)],
                        "modifie_le": [datetime(2024, 1, 2)],
                    }
                ),
                pd.DataFrame(
                    {
                        "id": ["source1_id1"],
                        "produitsdechets_acceptes": ["12345678"],
                        "nom_de_lorganisme": ["Eco1"],
                        "ecoorganisme": ["source1"],
                    }
                ),
                datetime(2024, 1, 1).date(),
            ),
        ],
    )
    def test_create_actors_cree_le(
        self,
        df_acteur,
        df_data_from_api,
        expected_cree_le,
    ):
        result = propose_acteur_changes(
            df_acteur=df_data_from_api,
            df_acteur_from_db=df_acteur,
        )
        df_result = result["df_acteur"]

        assert "cree_le" in df_result.columns
        assert df_result["cree_le"].notnull().all()
        assert df_result["cree_le"][0].date() == expected_cree_le
