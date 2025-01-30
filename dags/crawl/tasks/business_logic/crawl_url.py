import requests
from pydantic import BaseModel


class CrawlUrlModel(BaseModel):
    url: str
    timeout: int = 5
    was_success: bool = False
    status_code: int | None = 0
    error: str | None = None
    url_resolved: str = ""


def crawl_url(url: str, timeout: int = 5) -> CrawlUrlModel:
    try:
        resp = requests.get(url, timeout=timeout, allow_redirects=True)
        was_success = resp.ok
        return CrawlUrlModel(
            url=url,
            timeout=timeout,
            was_success=was_success,
            status_code=resp.status_code,
            error=None,
            url_resolved=resp.url,
        )
    except Exception as e:
        return CrawlUrlModel(
            url=url,
            timeout=timeout,
            was_success=False,
            status_code=None,
            error=str(e),
            url_resolved="",
        )
