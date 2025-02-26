"""Performs syntax checks URLs and tries
to fix them/propose alternatives following
some business logic (e.g. if http -> first try https)"""

import logging
import re
from urllib.parse import urlparse

import pandas as pd
from crawl.config.constants import (
    COL_DOMAINS_TO_TRY,
    COL_URL_ORIGINAL,
    COL_URLS_TO_TRY,
    SORT_COLS,
)
from utils import logging_utils as log
from utils.dataframes import df_sort

logger = logging.getLogger(__name__)


def url_is_valid(url) -> bool:
    """Checks if URL is valid"""
    try:
        parsed = urlparse(url)
        return all([parsed.scheme, parsed.netloc]) and parsed.scheme in [
            "http",
            "https",
        ]
    except Exception:
        return False


def url_domain_get(url: str) -> str | None:
    """Returns domain from URL"""
    try:
        parsed_url = urlparse(url)
        domain = parsed_url.netloc
        if ":" in domain:  # Remove port if present
            domain = domain.split(":")[0]
        domain = domain.strip()
        return domain if domain else None
    except Exception:
        return None


def url_to_dns_to_try(url: str) -> list[str] | None:
    """Returns domains to try from a URL,
    return None if no domain can be extracted"""
    domain = url_domain_get(url)
    return [domain] if domain else None


def url_protocol_fix(url: str) -> str:
    """Tries to fix protocol from URL as we
    have encountered several examples of urls
    with missing or extra : or /"""
    # Removing noise before http
    if not url.startswith("http"):
        url = re.sub(r".*http", r"http", url)

    # Adding https if protocol totally missing
    if not url.startswith("http"):
        # Case where URL can start with //
        if url.startswith("/"):
            url = f"https:{url}"
        else:
            url = f"https://{url}"

    # Fix too many :
    url = re.sub(r"::+", r":", url)
    # Fix too many /
    url = re.sub(r"///+", r"//", url)
    # Fix missing :
    url = re.sub(r"(https?)(/)", r"\1:\2", url)
    # Fix one or missing /
    url = re.sub(r"(https?:)/?([^/])", r"\1//\2", url)
    return url


def url_to_urls_to_try(url: str) -> list[str] | None:
    """Suggests URLs to try from a given URL,
    return None if no suggestion can be made"""
    if not (url or "").strip():
        return None

    # Base cleanup
    url = url.strip()

    # We want at least 1 dot for a domain name
    if "." not in url:
        return None

    url = url_protocol_fix(url)

    results = []

    # Keeping original URL if valid
    if url_is_valid(url):
        results.append(url)

    # We try the https version if missing
    if url.startswith("http://"):
        results.append(url.replace("http://", "https://"))

    valid = list(set([x for x in results if url_is_valid(x)]))
    prio = sorted(valid, key=lambda x: x.startswith("https://"), reverse=True)
    return prio


def crawl_urls_check_syntax(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Tries to check syntax on URLs, and returns 2 subsets:
    - urls we should try to crawl (= at least one suggestion)
    - urls we should discard (= no suggestion)
    """
    df[COL_URLS_TO_TRY] = df[COL_URL_ORIGINAL].apply(url_to_urls_to_try)
    df[COL_DOMAINS_TO_TRY] = df[COL_URLS_TO_TRY].apply(
        lambda x: url_to_dns_to_try(x[0]) if x else None
    )
    df_syntax_fail = df[
        (df[COL_URLS_TO_TRY].isnull()) | (df[COL_DOMAINS_TO_TRY].isnull())
    ]
    df_syntax_ok = df[df[COL_URLS_TO_TRY].notnull()]
    df_syntax_ok = df_sort(df_syntax_ok, sort_cols=SORT_COLS)
    df_syntax_fail = df_sort(df_syntax_fail, sort_cols=SORT_COLS)
    logging.info(log.banner_string("🏁 Résultat final de cette tâche"))
    log.preview_df_as_markdown("🟢 Syntaxes en succès", df_syntax_ok)
    log.preview_df_as_markdown("🔴 Syntaxes en échec", df_syntax_fail)
    return df_syntax_ok, df_syntax_fail
