import pandas as pd
import pytest
from sources.tasks.transform.transform_df import merge_duplicates


class TestMergeDuplicates:

    @pytest.mark.parametrize(
        "df, expected_df",
        [
            (
                pd.DataFrame(
                    {
                        "identifiant_unique": [1, 1],
                        "produitsdechets_acceptes": [
                            " Plastic Box | Metal | Aàèë l'test",
                            " Plastic Box | Metal | Aàèë l'test",
                        ],
                        "other_column": ["A", "B"],
                    }
                ),
                pd.DataFrame(
                    {
                        "identifiant_unique": [1],
                        "produitsdechets_acceptes": ["Aàèë l'test|Metal|Plastic Box"],
                        "other_column": ["A"],
                    }
                ),
            ),
            (
                pd.DataFrame(
                    {
                        "identifiant_unique": [1, 2, 3],
                        "produitsdechets_acceptes": [
                            "Plastic|Metal",
                            "Metal|Glass",
                            "Paper",
                        ],
                        "other_column": [
                            "A",
                            "B",
                            "C",
                        ],
                    }
                ),
                pd.DataFrame(
                    {
                        "identifiant_unique": [1, 2, 3],
                        "produitsdechets_acceptes": [
                            "Plastic|Metal",
                            "Metal|Glass",
                            "Paper",
                        ],
                        "other_column": [
                            "A",
                            "B",
                            "C",
                        ],
                    }
                ),
            ),
            (
                pd.DataFrame(
                    {
                        "identifiant_unique": [1, 1, 1],
                        "produitsdechets_acceptes": [
                            "Plastic|Metal",
                            "Metal|Glass",
                            "Paper",
                        ],
                        "other_column": [
                            "A",
                            "B",
                            "C",
                        ],
                    }
                ),
                pd.DataFrame(
                    {
                        "identifiant_unique": [1],
                        "produitsdechets_acceptes": ["Glass|Metal|Paper|Plastic"],
                        "other_column": ["A"],
                    }
                ),
            ),
            (
                pd.DataFrame(
                    {
                        "identifiant_unique": [1, 1, 2, 3, 3, 3],
                        "produitsdechets_acceptes": [
                            "Plastic|Metal",
                            "Metal|Glass",
                            "Paper",
                            "Glass|Plastic",
                            "Plastic|Metal",
                            "Metal",
                        ],
                        "other_column": ["A", "B", "C", "D", "E", "F"],
                    }
                ),
                pd.DataFrame(
                    {
                        "identifiant_unique": [1, 2, 3],
                        "produitsdechets_acceptes": [
                            "Glass|Metal|Plastic",
                            "Paper",
                            "Glass|Metal|Plastic",
                        ],
                        "other_column": ["A", "C", "D"],
                    }
                ),
            ),
        ],
    )
    def test_merge_duplicates(self, df, expected_df):

        result_df = merge_duplicates(df)

        result_df = result_df.sort_values(by="identifiant_unique").reset_index(
            drop=True
        )
        expected_df = expected_df.sort_values(by="identifiant_unique").reset_index(
            drop=True
        )

        pd.testing.assert_frame_equal(result_df, expected_df)
