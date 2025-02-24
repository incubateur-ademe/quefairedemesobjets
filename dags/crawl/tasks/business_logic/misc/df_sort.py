import pandas as pd


def df_sort(df: pd.DataFrame) -> pd.DataFrame:
    """Little utility to sort our dfs in a desired way
    throughout the pipeline without having to repeat
    ourselves everything"""
    cols_first = [
        "url_success",
        "was_success",
        "urls_tried",
        "url_original",
        "urls_to_try",
    ]
    cols = [x for x in cols_first if x in df.columns]
    cols += [x for x in df.columns if x not in cols]
    return df[cols]
