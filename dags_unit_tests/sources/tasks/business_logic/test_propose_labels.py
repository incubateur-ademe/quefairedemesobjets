import pandas as pd
import pytest
from sources.tasks.business_logic.propose_labels import propose_labels


class TestCeateLabels:

    def test_create_reparacteur_labels(
        self,
        acteurtype_id_by_code,
        labelqualite_id_by_code,
    ):
        df = propose_labels(
            df_actors=pd.DataFrame(
                {
                    "identifiant_unique": [1, 2],
                    "labels_etou_bonus": ["reparacteur", ""],
                    "acteur_type_id": [202, 202],
                }
            ),
            labelqualite_id_by_code=labelqualite_id_by_code,
            acteurtype_id_by_code=acteurtype_id_by_code,
        )

        expected_dataframe_with_reparacteur_label = pd.DataFrame(
            {
                "acteur_id": [1],
                "labelqualite_id": [3],
            }
        )

        pd.testing.assert_frame_equal(df, expected_dataframe_with_reparacteur_label)

    def test_create_ess_labels(
        self,
        acteurtype_id_by_code,
        labelqualite_id_by_code,
    ):
        df = propose_labels(
            df_actors=pd.DataFrame(
                {
                    "identifiant_unique": [1, 2],
                    "acteur_type_id": [201, 202],
                }
            ),
            labelqualite_id_by_code=labelqualite_id_by_code,
            acteurtype_id_by_code=acteurtype_id_by_code,
        )

        expected_dataframe_with_ess_label = pd.DataFrame(
            {
                "acteur_id": [1],
                "labelqualite_id": [1],
            }
        )

        pd.testing.assert_frame_equal(df, expected_dataframe_with_ess_label)

    @pytest.mark.parametrize(
        "code_label_bonus", ["LABEL_BONUS", "label_bonus", "Làbèl_bônùS"]
    )
    def test_create_bonus_reparation_labels(
        self,
        acteurtype_id_by_code,
        labelqualite_id_by_code,
        code_label_bonus,
    ):
        df = propose_labels(
            df_actors=pd.DataFrame(
                {
                    "identifiant_unique": [1, 2],
                    "labels_etou_bonus": [code_label_bonus, ""],
                    "acteur_type_id": [202, 202],
                }
            ),
            labelqualite_id_by_code=labelqualite_id_by_code,
            acteurtype_id_by_code=acteurtype_id_by_code,
        )

        expected_dataframe_with_bonus_reparation_label = pd.DataFrame(
            {
                "acteur_id": [1],
                "labelqualite_id": [2],
            }
        )

        pd.testing.assert_frame_equal(
            df, expected_dataframe_with_bonus_reparation_label
        )
