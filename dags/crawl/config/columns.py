"""Column names for Crawl DAG"""

from dataclasses import dataclass


@dataclass(frozen=True)
class COLS:
    # URL field as present in db
    URL_DB: str = "url"
    # which gets renamed to below during pipeline
    # to be more explicit and distinguish vs. all
    # other URL fields
    URL_ORIGIN: str = "url"
    COUNT: str = "count"
    URL_HTTPS: str = "url_is_https_version"
    URLS_TO_TRY: str = "urls_to_try"
    URLS_RESULTS: str = "urls_results"
    CRAWL_WAS_SUCCESS: str = "crawl_was_success"
    CRAWL_TRIES_COUNT: str = "crawl_tries_count"
    CRAWL_URL_SUCCESS: str = "crawl_url_success"
    DOMAINS_TO_TRY: str = "domains_to_try"
    DOMAINS_RESULTS: str = "domains_results"
    DNS_OK: str = "dns_ok"
    ACTEURS: str = "acteurs"
    SUGGEST_VALUE: str = "suggest_value"
    COHORT: str = "suggest_cohort"
    ID: str = "identifiant_unique"
