import pandas as pd
from pandas._testing import assert_frame_equal
from utils.dag_ingest_validated_utils import process_many2many_df


def test_process_labels_valid_column():
    data = {
        "labels": [
            {"acteur_id": 1, "labelqualite_id": 100},
            {"acteur_id": 2, "labelqualite_id": 101},
            {"acteur_id": 3, "labelqualite_id": 102},
        ]
    }
    df = pd.DataFrame(data)
    expected_data = {"acteur_id": [1, 2, 3], "labelqualite_id": [100, 101, 102]}
    expected_df = pd.DataFrame(expected_data)

    result_df = process_many2many_df(df, "labels")
    assert_frame_equal(result_df, expected_df)


def test_process_many2many_df_missing_column():
    data = {"other_column": [10, 20, 30, 40]}
    df = pd.DataFrame(data)
    expected_df = pd.DataFrame(columns=["acteur_id", "labelqualite_id"])

    result_df = process_many2many_df(df, "missing_column")
    assert_frame_equal(result_df, expected_df)


def test_process_many2many_df_empty_dataframe():
    df = pd.DataFrame(columns=["labels"])
    expected_df = pd.DataFrame(columns=["acteur_id", "labelqualite_id"])

    result_df = process_many2many_df(df, "labels")
    assert_frame_equal(result_df, expected_df)
