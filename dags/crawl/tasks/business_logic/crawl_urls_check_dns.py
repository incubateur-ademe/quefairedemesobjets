"""Performs DNS checks on the domains of the URLs"""

import logging
import socket

import pandas as pd
from crawl.config.constants import (
    COL_DOMAIN_SUCCESS,
    COL_DOMAINS_RESULTS,
    COL_DOMAINS_TO_TRY,
    COL_URLS_TO_TRY,
)
from crawl.tasks.business_logic.crawl_urls_check_syntax import url_domain_get
from utils import logging_utils as log

logger = logging.getLogger(__name__)


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

    df[COL_DOMAINS_TO_TRY] = df[COL_URLS_TO_TRY].apply(
        lambda urls: list(set([url_domain_get(x) for x in urls])) if urls else None
    )

    df[COL_DOMAINS_RESULTS] = df[COL_DOMAINS_TO_TRY].apply(
        lambda domains: (
            [{"domain": x, "is_ok": dns_is_ok(x)} for x in domains] if domains else None
        )
    )

    # We use a loop so we can show progress
    cnt, cnt_rows = 0, len(df)
    for index, row in df.iterrows():
        cnt += 1
        domains = row[COL_DOMAINS_TO_TRY]
        if not domains:
            continue
        logger.info(log.progress_string(cnt, cnt_rows))
        results = [{"domain": x, "is_ok": dns_is_ok(x)} for x in domains]
        msg = [f"{x['domain']} -> {'🟢' if x['is_ok'] else '🔴'}" for x in results]
        logger.info(f"🔍 Domaines: {msg}")
        df.at[index, COL_DOMAINS_RESULTS] = results

    df[COL_DOMAIN_SUCCESS] = df[COL_DOMAINS_RESULTS].apply(
        lambda domains: (
            True if domains and any([x["is_ok"] for x in domains]) else False
        )
    )

    df_dns_ok = df[df[COL_DOMAIN_SUCCESS]]
    df_dns_fail = df[~df[COL_DOMAIN_SUCCESS]]

    logging.info(log.banner_string("🏁 Résultat final de cette tâche"))
    log.preview_df_as_markdown("🟢 Domaines en succès", df_dns_ok)
    log.preview_df_as_markdown("🔴 Domaines en échec", df_dns_fail)
    return df_dns_ok, df_dns_fail
