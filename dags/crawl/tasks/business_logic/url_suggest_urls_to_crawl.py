import re
from urllib.parse import urlparse


def is_valid_url(url):
    parsed = urlparse(url)
    return all([parsed.scheme, parsed.netloc]) and parsed.scheme in ["http", "https"]


def url_suggest_urls_to_crawl(url: str) -> list[str] | None:
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
