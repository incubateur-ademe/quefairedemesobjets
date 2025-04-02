"""Constants for suggestions cohorts for Crawl DAG"""

from dataclasses import dataclass


@dataclass(frozen=True)
class COHORTS:
    # Cohorts we will propose as suggestions
    SYNTAX_FAIL = "🔴 Syntaxe invalide → mise à vide"
    DNS_FAIL = "🔴 Domaine inaccessible → mise à vide"
    CRAWL_FAIL = "🔴 URL inaccessible → mise à vide"
    CRAWL_DIFF_STANDARD = "🟢 URL diff standard (ex: http->https) → nouvelle proposée"
    CRAWL_DIFF_OTHER = "🟠 URL diff non-standard → nouvelle proposée"

    # Cohorts for display purposes only
    SYNTAX_OK = "🟢 Syntaxe en succès"
    DNS_OK = "🟢 Domaines en succès"
    CRAWL_OK_SAME = "🟢 URL en succès ET inchangée"
