import pandas as pd
from sources.tasks.business_logic.propose_labels import propose_labels


class TestCeateLabels:

    def test_create_reparacteur_labels(
        self,
        labelqualite_id_by_code,
    ):
        df = propose_labels(
            df_acteur=pd.DataFrame(
                {
                    "identifiant_unique": [1, 2],
                    "label_codes": [["label_bonus"], []],
                    "acteur_type_id": [202, 202],
                }
            ),
            labelqualite_id_by_code=labelqualite_id_by_code,
        )

        expected_dataframe_with_reparacteur_label = pd.DataFrame(
            {
                "acteur_id": [1],
                "labelqualite_id": [2],
            }
        )

        pd.testing.assert_frame_equal(df, expected_dataframe_with_reparacteur_label)
