"""Utilities to avoid repeating ourselves when dealing
with dataframes in our pipelines"""

import logging

import pandas as pd
from utils import logging_utils as log

logger = logging.getLogger(__name__)


def df_filter(df: pd.DataFrame, filters: list[dict]) -> pd.DataFrame:
    """Filters a dataframe given some filters"""
    log.preview_df_as_markdown("Données SANS filtre", df)
    log.preview("Filtres", filters)
    filter_applied = False
    if not df.empty:
        for filter in filters:
            filter_applied = True
            field = filter["field"]
            operator = filter["operator"]
            value = filter["value"]
            logger.info(f"\n🔽 Filtre sur {field=} {operator=} {value=}")
            logger.info(f"Avant filtre : {df.shape[0]} lignes")

            # Filtering
            if filter["operator"] == "equals":
                logger.info(f"Filtre sur {field} EQUALS {value}")
                df = df[df[field] == value].copy()
            elif filter["operator"] == "contains":
                df = df[df[field].str.contains(value, regex=True, case=False)].copy()
            elif filter["operator"] == "in":
                if value and len(value) > 0:
                    df = df[df[field].isin(value)].copy()
            else:
                raise NotImplementedError(f"{filter['operator']=} non implémenté")

            logger.info(f"Après filtre : {df.shape[0]} lignes")

    if filter_applied:
        log.preview_df_as_markdown("Données APRES filtre(s)", df)
    else:
        logger.info("Aucun filtre appliqué")

    return df


def df_sort(
    df: pd.DataFrame, sort_rows: list[str] = [], sort_cols: list[str] = []
) -> pd.DataFrame:
    """Sorts rows & columns of df based on desired order vs. what's available
    (e.g. useful to debug DFs throughout DAGs without worrying about what's
    in them at each step)"""
    if df.empty:
        return df

    # Only sorting if desired present
    sort_rows = [x for x in sort_rows if x in df.columns]
    if sort_rows:
        df = df.sort_values(by=sort_rows)
    # First by desired order, then by whatever is left
    sort_cols = [x for x in sort_cols if x in df.columns]
    sort_cols += [x for x in df.columns if x not in sort_cols]
    return df[sort_cols]


def df_none_or_empty(df: pd.DataFrame) -> bool:
    """When working with Airflow XCOM it's common
    to obtain None values if some tasks were skipped,
    having a dedicated function serves as a reminder
    of this common pattern that might not even get a df"""
    return df is None or df.empty


def df_col_count_lists(df: pd.DataFrame, col: str) -> int:
    """Total count of items in list-type columns,
    with the catch to return integer (np64 by default)
    to avoid JSON serialization issues"""
    return int(df[col].apply(len).sum())


def df_split_on_filter(
    df: pd.DataFrame, filter: pd.Series
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Splits a dataframe into two dataframes based on a filter,
    while ensuring the two dfs are mutually exclusive and complementary"""
    dfa = df[filter].copy()
    dfb = df[~filter].copy()
    assert len(dfa) + len(dfb) == len(df)
    assert set(dfa.index).isdisjoint(set(dfb.index))
    return dfa, dfb


def df_col_assert_get_unique(df: pd.DataFrame, col: str) -> str:
    """Asserts that a column is unique and returns its value,
    useful when dealing with single-value columns like cohorts
    to ensure we're not mixing things up"""
    uniques = df[col].unique()
    if len(uniques) != 1:
        raise ValueError(f"Colonne {col} doit être unique: {uniques}")
    return uniques[0]


def df_discard_if_col_vals_frequent(
    df: pd.DataFrame, col: str, threshold: int
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Discards rows which have col value appear too frequently
    across dataframe (e.g. useful in crawling to discard URLs
    for frequent domains)"""
    value_counts = df[col].value_counts()
    filter_discard = df[col].isin(value_counts[value_counts >= threshold].index)
    df_discarded, df = df_split_on_filter(df, filter_discard)
    if not df_discarded.empty:
        msg = f"🔴 Lignes supprimées car colonne={col} répétée >= {threshold} fois"
        log.preview_df_as_markdown(msg, df_discarded)
    return df, df_discarded


def dfs_assert_add_up_to_df(dfs: list[pd.DataFrame], df: pd.DataFrame) -> None:
    """Asserts that the sum of the dfs equals the original df
    (e.g. using in crawling DAG where we end up with 4 crawling cohorts
    and want to ensure our filters were all properly exclusive/complementary)"""
    len_dfs = sum(len(d) for d in dfs)
    len_df = len(df)
    if len_dfs != len_df:
        raise ValueError(f"Somme lignes des dfs {len_dfs} != df originale {len_df}")
    if set(df.index) != set(index for d in dfs for index in d.index):
        raise ValueError("Indexes des dfs ne correspondent pas à l'original")


def df_add_original_columns(
    df_modify: pd.DataFrame,
    df_original: pd.DataFrame,
    on: str = "identifiant_unique",
) -> pd.DataFrame:
    """Add columns from original missing in modified dataframe"""
    cols_add = [x for x in df_original.columns if x not in df_modify.columns]
    logger.info(f"Colonnes à rajouter: {cols_add} via {on}")
    cols = ["identifiant_unique"] + cols_add
    return df_modify.merge(df_original[cols], on="identifiant_unique", how="left")
