from datetime import datetime

import pandas as pd
import pytest
from shapely import wkb
from shapely.geometry import Point
from sources.tasks.business_logic.propose_acteur_changes import propose_acteur_changes


class TestProposeActeurChangesCreeLe:
    @pytest.mark.parametrize(
        "df_acteur, df_data_from_api, expected_cree_le",
        [
            # Empty acteur
            (
                pd.DataFrame(
                    columns=[
                        "identifiant_unique",
                        "source_id",
                        "statut",
                        "cree_le",
                        "modifie_le",
                    ]
                ),
                pd.DataFrame(
                    {
                        "identifiant_unique": ["source1_id1"],
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
                        "identifiant_unique": ["source1_id1"],
                        "source_id": [101],
                        "statut": ["ACTIF"],
                        "cree_le": [datetime(2024, 1, 1)],
                        "modifie_le": [datetime(2024, 1, 2)],
                    }
                ),
                pd.DataFrame(
                    {
                        "identifiant_unique": ["source1_id1"],
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
            df=df_data_from_api,
            df_acteurs=df_acteur,
        )
        df_result = result["df"]

        assert "cree_le" in df_result.columns
        assert df_result["cree_le"].notnull().all()
        assert df_result["cree_le"][0].date() == expected_cree_le


class TestActorsLocation:
    @pytest.mark.parametrize(
        "latitude, longitude",
        [
            (48.8566, 2.3522),
            ("48.8566", "2.3522"),
            ("48,8566", "2,3522"),
        ],
    )
    def test_create_actors_location(
        self,
        df_empty_acteurs_from_db,
        latitude,
        longitude,
    ):
        result = propose_acteur_changes(
            df=pd.DataFrame(
                {
                    "identifiant_unique": ["1"],
                    "latitude": [latitude],
                    "longitude": [longitude],
                }
            ),
            df_acteurs=df_empty_acteurs_from_db,
        )
        df_result = result["df"]

        expected_location = wkb.dumps(Point(2.3522, 48.8566)).hex()

        assert df_result["location"].iloc[0] == expected_location
