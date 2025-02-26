"""Utilities to avoid repeating ourselves when dealing
with dataframes in our pipelines"""

import pandas as pd


def df_sort(
    df: pd.DataFrame, sort_rows: list[str] = [], sort_cols: list[str] = []
) -> pd.DataFrame:
    """Sorts a dataframe according to rows & column order,
    while keeping other columns and not crashing if some
    columns are missing. This is useful in pipelines like
    clustering where dataframes go through various stages
    (normalization, clustering, etc) and we want a convenient
    way of displaying dfs without worrying about their state.

    note: for clustering we want sort_rows to reflect clustering but
    we want sort_cols to prioritize certain debug columns (statut)"""
    # Only sorting if desired present
    sort_rows = [x for x in sort_rows if x in df.columns]
    if sort_rows:
        df = df.sort_values(by=sort_rows)
    # First by desired order, then by whatever is left
    sort_cols = [x for x in sort_cols if x in df.columns]
    sort_cols += [x for x in df.columns if x not in sort_cols]
    return df[sort_cols]
