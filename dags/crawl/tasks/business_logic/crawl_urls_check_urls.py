"""Performs crawl checks on the URLs"""

import logging

import pandas as pd
import requests
from crawl.config.constants import COL_URLS_RESULTS, SORT_COLS
from pydantic import BaseModel
from utils import logging_utils as log
from utils.dataframes import df_sort

logger = logging.getLogger(__name__)

# Bear minimum to pretend we're a browser
USER_AGENT = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko)"


class CrawlUrlModel(BaseModel):
    url: str
    timeout: int = 5
    was_success: bool = False
    status_code: int | None = 0
    error: str | None = None
    url_recheckd: str = ""


def crawl_url(url: str, timeout: int = 5) -> CrawlUrlModel:
    try:
        resp = requests.get(
            url,
            timeout=timeout,
            allow_redirects=True,
            headers={"User-Agent": USER_AGENT},
        )
        was_success = resp.ok
        return CrawlUrlModel(
            url=url,
            timeout=timeout,
            was_success=was_success,
            status_code=resp.status_code,
            error=None,
            url_recheckd=resp.url,
        )
    except Exception as e:
        return CrawlUrlModel(
            url=url,
            timeout=timeout,
            was_success=False,
            status_code=None,
            error=str(e),
            url_recheckd="",
        )


def crawl_urls_check_reach(
    df: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    log.preview_df_as_markdown("🔎 URLs qu'on va essayer de parcourir", df)
    df["was_success"] = False
    df["urls_tried"] = 0
    df["url_success"] = None
    df[COL_URLS_RESULTS] = df["urls_to_try"].apply(lambda x: [])
    for _, row in df.iterrows():
        if not row["urls_to_try"]:
            continue
        for url in row["urls_to_try"]:
            logger.info(f"🔍 CRAWL: {url}")
            result: CrawlUrlModel = crawl_url(url)
            df.at[_, "urls_tried"] += 1
            df.at[_, COL_URLS_RESULTS].append(result.model_dump())
            if result.was_success:
                df.at[_, "was_success"] = True
                df.at[_, "url_success"] = result.url_recheckd
                break

    # Ordering columns for easier review
    cols_urls = ["url_success", "url_original", "urls_to_try"]
    cols_all = cols_urls + [x for x in df.columns if x not in cols_urls]
    df = df[cols_all]

    df_urls_ok_same = df[
        (df["was_success"]) & (df["url_original"] == df["url_success"])
    ]
    df_urls_ok_diff = df[
        (df["was_success"]) & (df["url_original"] != df["url_success"])
    ]
    df_urls_fail = df[~df["was_success"]]
    df_urls_ok_same = df_sort(df_urls_ok_same, sort_cols=SORT_COLS)
    df_urls_ok_diff = df_sort(df_urls_ok_diff, sort_cols=SORT_COLS)
    df_urls_fail = df_sort(df_urls_fail, sort_cols=SORT_COLS)

    logging.info(log.banner_string("🏁 Résultat final de cette tâche"))
    log.preview_df_as_markdown("🟢 URLs en succès ET inchangées", df_urls_ok_same)
    log.preview_df_as_markdown("🟡 URLs en succès ET différentes", df_urls_ok_diff)
    log.preview_df_as_markdown("🔴 URLs en échec", df_urls_fail)
    return df_urls_ok_same, df_urls_ok_diff, df_urls_fail
