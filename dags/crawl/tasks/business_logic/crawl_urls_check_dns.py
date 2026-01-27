"""Performs DNS checks on the domains of the URLs"""

import logging
import socket
from functools import lru_cache

import pandas as pd
from crawl.config.cohorts import COHORTS
from crawl.config.columns import COLS
from crawl.tasks.business_logic.crawl_urls_check_syntax import url_domain_get
from sources.config.shared_constants import EMPTY_ACTEUR_FIELD
from utils import logging_utils as log
from utils.dataframes import df_split_on_filter

logger = logging.getLogger(__name__)


# To avoid re-checking the same domain
# when we have sorted URLs by domain
@lru_cache(maxsize=1)
def dns_is_ok(domain: str) -> bool:
    """Checks if a domain is reachable so we don't
    waste time trying to crawl URLs for unreachable domains"""
    if domain is None or not domain.strip():
        return False
    try:
        socket.gethostbyname(domain)
        return True
    except Exception:
        return False


def crawl_urls_check_dns(
    df: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Checks if the domains of the URLs are reachable,
    returns 2 sub-dataframes (working/failing)"""

    log.preview_df_as_markdown("🔎 Domaines à résoudre", df)

    df[COLS.DOMAINS_TO_TRY] = df[COLS.URLS_TO_TRY].apply(
        lambda urls: list(set([url_domain_get(x) for x in urls if x])) if urls else None
    )

    # Only keep rows with at least 1 domain to try
    df = df[df[COLS.DOMAINS_TO_TRY].notnull() & df[COLS.DOMAINS_TO_TRY].apply(bool)]

    # Sort by 1st domain to maximize DNS cache hits
    df = df.sort_values(by=COLS.DOMAINS_TO_TRY, key=lambda x: x.str[0])

    # We use a loop so we can show progress
    total = len(df)
    for counter, (index, row) in enumerate(df.iterrows(), start=1):
        domains = row[COLS.DOMAINS_TO_TRY]
        logger.info(log.progress_string(counter, total))
        results = [{"domain": x, "is_ok": dns_is_ok(x)} for x in domains]
        msg = [f"{x['domain']} -> {'🟢' if x['is_ok'] else '🔴'}" for x in results]
        logger.info(f"🔍 Domaines: {msg}")
        df.at[index, COLS.DOMAINS_RESULTS] = results

    df[COLS.DNS_OK] = df[COLS.DOMAINS_RESULTS].apply(
        lambda domains: (
            True if domains and any([x["is_ok"] for x in domains]) else False
        )
    )

    # Splitting success vs. failure
    filter_dns_ok = df[COLS.DNS_OK]
    df_dns_ok, df_dns_fail = df_split_on_filter(df, filter_dns_ok)
    df_dns_ok[COLS.COHORT] = COHORTS.DNS_OK
    df_dns_fail[COLS.COHORT] = COHORTS.DNS_FAIL

    # Assigning suggestion values
    df_dns_fail[COLS.SUGGEST_VALUE] = EMPTY_ACTEUR_FIELD

    logger.info(log.banner_string("🏁 Résultat final de cette tâche"))
    log.preview_df_as_markdown(COHORTS.DNS_OK, df_dns_ok)
    log.preview_df_as_markdown(COHORTS.DNS_FAIL, df_dns_fail)
    return df_dns_ok, df_dns_fail
