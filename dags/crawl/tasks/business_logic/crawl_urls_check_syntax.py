"""Perform syntax checks URLs and tries
to fix them/propose alternatives following
some business logic (e.g. if http -> first try https)"""

import logging
import re
from urllib.parse import urlparse

import pandas as pd
from crawl.config.cohorts import COHORTS
from crawl.config.columns import COLS
from crawl.config.constants import SORT_COLS
from sources.config.shared_constants import EMPTY_ACTEUR_FIELD
from utils import logging_utils as log
from utils.dataframes import df_sort, df_split_on_filter

logger = logging.getLogger(__name__)


def url_is_valid(url) -> bool:
    """Checks if URL is valid"""
    try:
        # Not using urlparse which was too permissive
        # (e.g. it accepts "http://" only)
        # Using a regex also allows to be more specific
        # with what we consider a valid URL vs. pure technical
        # aspect
        pattern = re.compile(
            r"^(https?):\/\/"  # Protocol (http, https)
            r"([a-zA-Z0-9_-]+\.)+"  # Domain name
            r"[a-zA-Z]{2,}"  # Top-level domain (e.g., .com, .org)
            r"(\/[^\s]*)?$"  # Optional path
        )
        return re.match(pattern, url) is not None
    except Exception:
        return False


def urls_are_diff_standard(url1, url2) -> bool:
    """Check if 2 URLs a "standard" redirection of each other, defined as:
    - case insensitive
    - http vs. https
    - www vs. no www
    - tolerate trailing slashes
    """
    if not url1 or not url1.strip() or not url2 or not url2.strip():
        return False
    url1 = re.sub(r"^https?://(www\.)?|/$", "", url1.strip(), flags=re.I).lower()
    url2 = re.sub(r"^https?://(www\.)?|/$", "", url2.strip(), flags=re.I).lower()
    return url1 == url2


def url_domain_get(url: str) -> str | None:
    """Returns domain from URL"""
    try:
        is_valid = url_is_valid(url)
        if not is_valid:
            return None
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


def url_fix_protocol(url: str) -> str:
    """Tries to fix protocol from URL as we
    have encountered several examples of urls
    with missing or extra : or /"""
    # Removing noise before http
    if not url.startswith("http"):
        url = re.sub(r".*http", r"http", url)

    # Duplicate protocols (replace up to 2nd http takes care of optional s)
    url = re.sub(r"(https?(?:://)?http)", r"http", url)

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


def url_fix_www(url: str) -> str:
    """Attempts to fix the www as we have had many cases of:
    - missing dot
    - too many or too few www"""
    return re.sub(r"^(https?://)((?:ww\.?|wwww+\.?))([^w])", r"\1www.\3", url)


def url_fix_language(url: str) -> str:
    """Replacing the common English language code
    coming out of using a crawler"""
    return re.sub("/en/?$", "/", url)


def url_fix_consecutive_dots(url: str) -> str:
    """Fix multiple consecutive dots"""
    return re.sub(r"\.{2,}", ".", url)


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

    # Various fixes
    url = url_fix_protocol(url)
    url = url_fix_www(url)
    url = url_fix_consecutive_dots(url)
    url = url_fix_language(url)

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
    df[COLS.URLS_TO_TRY] = df[COLS.URL_ORIGIN].apply(url_to_urls_to_try)
    df[COLS.DOMAINS_TO_TRY] = df[COLS.URLS_TO_TRY].apply(
        lambda x: url_to_dns_to_try(x[0]) if x else None
    )

    # Splitting success vs. failure
    filter_syntax = (df[COLS.URLS_TO_TRY].notnull()) & (
        df[COLS.DOMAINS_TO_TRY].notnull()
    )
    df_syntax_ok, df_syntax_fail = df_split_on_filter(df, filter_syntax)
    df_syntax_ok[COLS.COHORT] = COHORTS.SYNTAX_OK
    df_syntax_fail[COLS.COHORT] = COHORTS.SYNTAX_FAIL

    #  Assigning suggestion values
    df_syntax_fail[COLS.SUGGEST_VALUE] = EMPTY_ACTEUR_FIELD

    # Sorting
    df_syntax_ok = df_sort(df_syntax_ok, sort_cols=SORT_COLS)
    df_syntax_fail = df_sort(df_syntax_fail, sort_cols=SORT_COLS)

    # Debug
    logger.info(log.banner_string("🏁 Résultat final de cette tâche"))
    log.preview_df_as_markdown(COHORTS.SYNTAX_OK, df_syntax_ok)
    log.preview_df_as_markdown(COHORTS.SYNTAX_FAIL, df_syntax_fail)
    return df_syntax_ok, df_syntax_fail
