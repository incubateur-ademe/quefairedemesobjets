import pandas as pd
from crawl.tasks.business_logic.misc.df_sort import df_sort


def crawl_urls_candidates_groupby_url(
    df: pd.DataFrame, col_groupby: str, col_grouped_data: str
) -> pd.DataFrame:
    """Grouping by URLs whilst packing all the other data
    into a list of dicts"""
    df = (
        df.groupby(col_groupby)
        .apply(lambda x: x.drop(columns=col_groupby).to_dict(orient="records"))
        .reset_index()
    )
    df.columns = [col_groupby, col_grouped_data]
    return df_sort(df)
