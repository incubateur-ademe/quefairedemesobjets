import re
from urllib.parse import urlparse

import pandas as pd
from crawl.config.constants import COL_URL_ORIGINAL, COL_URLS_TO_TRY
from crawl.tasks.business_logic.misc.df_sort import df_sort


def is_valid_url(url):
    parsed = urlparse(url)
    return all([parsed.scheme, parsed.netloc]) and parsed.scheme in ["http", "https"]


def url_solve_syntax(url: str) -> list[str] | None:
    """Suggère des remplacements d'URL sur une base syntaxique"""
    if not (url or "").strip():
        return None

    # On supprime les espaces en début et fin
    url = url.strip()

    # Si pas de nom de domaine, on ne peut rien faire
    if "." not in url:
        return None

    results = []

    if is_valid_url(url):
        results.append(url)

    # On supprime tout ce qui vient avant https://
    if not url.startswith("http"):
        url = re.sub(r".*(https?://.*)", r"\1", url)
        results.append(url)

    # On rajoute https:// si manquant
    if not url.startswith("http"):
        url = f"https://{url}"
        results.append(url)

    # On remplace http:// par https://
    if url.startswith("http://"):
        url = url.replace("http://", "https://")
        results.append(url)

    valid = list(set([x for x in results if is_valid_url(x)]))
    prio = sorted(valid, key=lambda x: x.startswith("https://"), reverse=True)
    return prio


def crawl_urls_solve_syntax(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Tries to solve syntax on URLs, and returns 2 subsets:
    - urls we should try to crawl (= at least one suggestion)
    - urls we should discard (= no suggestion)
    """
    df[COL_URLS_TO_TRY] = df[COL_URL_ORIGINAL].apply(url_solve_syntax)
    df_discarded = df[df[COL_URLS_TO_TRY].isnull()]
    df_try = df[df[COL_URLS_TO_TRY].notnull()]
    return df_sort(df_try), df_sort(df_discarded)
