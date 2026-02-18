"""Performs crawl checks on the URLs"""

import logging

import pandas as pd
import requests
from crawl.config.cohorts import COHORTS
from crawl.config.columns import COLS
from crawl.config.constants import SORT_COLS
from crawl.tasks.business_logic.crawl_urls_check_syntax import urls_are_diff_standard
from pydantic import BaseModel
from utils import logging_utils as log
from utils.dataframes import (
    df_discard_if_col_vals_frequent,
    df_sort,
    df_split_on_filter,
    dfs_assert_add_up_to_df,
)
from utils.django import django_setup_full

django_setup_full()
logger = logging.getLogger(__name__)

# Bear minimum to pretend we're a browser
USER_AGENT = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko)"
HEADERS = {
    "User-Agent": USER_AGENT,
    "Accept-Language": "fr;q=1.0, *;q=0.0",
}


class CrawlUrlModel(BaseModel):
    url: str
    timeout: int = 5
    was_success: bool = False
    status_code: int | None = 0
    error: str | None = None
    url_reached: str = ""


def crawl_url(url: str, timeout: int = 5) -> CrawlUrlModel:
    try:
        resp = requests.get(
            url,
            timeout=timeout,
            allow_redirects=True,
            headers=HEADERS,
        )
        was_success = resp.ok
        return CrawlUrlModel(
            url=url,
            timeout=timeout,
            was_success=was_success,
            status_code=resp.status_code,
            error=None,
            url_reached=resp.url,
        )
    except Exception as e:
        return CrawlUrlModel(
            url=url,
            timeout=timeout,
            was_success=False,
            status_code=None,
            error=str(e),
            url_reached="",
        )


def df_exclude_frequent_domains(df: pd.DataFrame, n: int = 20) -> pd.DataFrame:
    """Excludes domains which appear for many URLs, as these are typically
    big sites such as social media OR retailers and we don't want to crawl
    them as it is with our basic crawling infrastructure"""
    df["domain_first"] = df[COLS.DOMAINS_TO_TRY].apply(lambda x: x[0])
    df, _ = df_discard_if_col_vals_frequent(df, "domain_first", 10)
    return df


def df_check_crawl(df: pd.DataFrame) -> pd.DataFrame:
    """Performs the crawling of URLs on the input df"""
    log.preview_df_as_markdown("🔎 URLs qu'on va essayer de parcourir", df)
    df[COLS.CRAWL_WAS_SUCCESS] = False
    df[COLS.CRAWL_TRIES_COUNT] = 0
    df[COLS.CRAWL_URL_SUCCESS] = None
    df[COLS.URLS_RESULTS] = df[COLS.URLS_TO_TRY].apply(lambda x: [])
    total = len(df)
    for counter, (index, row) in enumerate(df.iterrows(), start=1):
        logger.info(log.progress_string(counter, total))
        for url in row[COLS.URLS_TO_TRY]:
            logger.info(f"🔍 CRAWL: {url}")
            result: CrawlUrlModel = crawl_url(url)
            df.at[index, COLS.CRAWL_TRIES_COUNT] += 1
            df.at[index, COLS.URLS_RESULTS].append(result.model_dump())
            if result.was_success:
                df.at[index, COLS.CRAWL_WAS_SUCCESS] = True
                df.at[index, COLS.CRAWL_URL_SUCCESS] = result.url_reached
                break
    return df


def df_cohorts_split(
    df: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Takes the df output of df_check_crawl and splits it into cohorts"""

    from core.models.constants import EMPTY_ACTEUR_FIELD

    # TODO: the nested ifs below aren't great but needed since pandas won't
    # allow certain operations on empty dataframes (see df_ok_diff.apply)
    # and we have several successive splitings to create cohorts. Maybe
    # we could refactor this to be more elegant.
    # Final df for each cohort: init to None due to nested
    # if structure meaning certain dfs might never be set
    empty = pd.DataFrame()
    df_ok_same, df_ok_diff_standard, df_ok_diff_other = empty, empty, empty

    # Splitting success vs. failure
    filter_success = df[COLS.CRAWL_WAS_SUCCESS]
    df_crawl_ok, df_crawl_fail = df_split_on_filter(df, filter_success)

    # Managing all aspects of failure only if some
    if not df_crawl_fail.empty:
        df_crawl_fail[COLS.SUGGEST_VALUE] = EMPTY_ACTEUR_FIELD
        df_crawl_fail[COLS.COHORT] = COHORTS.CRAWL_FAIL
        df_crawl_fail = df_sort(df_crawl_fail, sort_cols=SORT_COLS)

    # Managing all aspects of success only if some
    if not df_crawl_ok.empty:
        df_crawl_ok[COLS.SUGGEST_VALUE] = df_crawl_ok[COLS.CRAWL_URL_SUCCESS]
        filter_same = (
            df_crawl_ok[COLS.URL_ORIGIN] == df_crawl_ok[COLS.CRAWL_URL_SUCCESS]
        )
        df_ok_same, df_ok_diff = df_split_on_filter(df_crawl_ok, filter_same)

        if not df_ok_same.empty:
            df_ok_same[COLS.COHORT] = COHORTS.CRAWL_OK_SAME

        if not df_ok_diff.empty:
            # We further split successful but different URLs into:
            # - those which are just HTTP -> HTTPS redirects
            # - those which are more subtantially different
            df_ok_diff[COLS.URL_HTTPS] = df_ok_diff.apply(
                lambda x: urls_are_diff_standard(
                    x[COLS.URL_ORIGIN], x[COLS.CRAWL_URL_SUCCESS]
                ),
                axis=1,
            )
            filter_https = df_ok_diff[COLS.URL_HTTPS]
            df_ok_diff_standard, df_ok_diff_other = df_split_on_filter(
                df_ok_diff, filter_https
            )

            # Final cohorts
            df_ok_diff_standard[COLS.COHORT] = COHORTS.CRAWL_DIFF_STANDARD
            df_ok_diff_other[COLS.COHORT] = COHORTS.CRAWL_DIFF_OTHER

            # Sorting
            df_ok_diff_standard = df_sort(df_ok_diff_standard, sort_cols=SORT_COLS)
            df_ok_diff_other = df_sort(df_ok_diff_other, sort_cols=SORT_COLS)

    logger.info(log.banner_string("🏁 Résultat final de cette tâche"))
    log.preview_df_as_markdown(COHORTS.CRAWL_OK_SAME, df_ok_same)
    log.preview_df_as_markdown(COHORTS.CRAWL_DIFF_STANDARD, df_ok_diff_standard)
    log.preview_df_as_markdown(COHORTS.CRAWL_DIFF_OTHER, df_ok_diff_other)
    log.preview_df_as_markdown(COHORTS.CRAWL_FAIL, df_crawl_fail)

    # Validation: all cohorts should add up to the original df
    dfs_assert_add_up_to_df(
        dfs=[df_ok_same, df_ok_diff_standard, df_ok_diff_other, df_crawl_fail],
        df=df,
    )

    # We only return what we make suggestions for, thus df_ok_same left out
    return df_ok_diff_standard, df_ok_diff_other, df_crawl_fail


def crawl_urls_check_crawl(
    df: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Applies the overall crawling logic to a df of URLs"""

    # We work on URLs for which DNS is OK (which implied syntax
    # is also OK) and thus we have at last 1 URL to try
    df = df[df[COLS.URLS_TO_TRY].notnull()].copy()

    # Excluding frequent domains
    df = df_exclude_frequent_domains(df)

    # Crawling
    df = df_check_crawl(df)

    # Splitting into cohorts
    return df_cohorts_split(df)
