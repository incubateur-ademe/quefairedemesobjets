"""Task IDs for Crawl DAG"""

from dataclasses import dataclass


@dataclass(frozen=True)
class TASKS:
    READ: str = "crawl_urls_read_urls_from_db"
    CHECK_SYNTAX: str = "crawl_urls_check_syntax"
    CHECK_DNS: str = "crawl_urls_check_dns"
    CHECK_CRAWL: str = "crawl_urls_check_crawl"
    SUGGEST_SYNTAX_FAIL: str = "crawl_urls_suggest_syntax_fail"
    SUGGEST_DNS_FAIL: str = "crawl_urls_suggest_dns_fail"
    SUGGEST_CRAWL_DIFF_STANDARD: str = "crawl_urls_suggest_crawl_diff_standard"
    SUGGEST_CRAWL_DIFF_OTHER: str = "crawl_urls_suggest_crawl_diff_other"
