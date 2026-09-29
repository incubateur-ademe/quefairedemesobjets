"""Saved PostHog insights as a source of key result values."""

import logging
from datetime import date

import requests
from django import forms
from django.conf import settings
from django.core.cache import cache

from stats.utils import parse_date

logger = logging.getLogger(__name__)

TIMEOUT_SECONDS = 60
INSIGHTS_CACHE_SECONDS = 600


def _api(path: str, **kwargs) -> dict:
    stats = settings.STATS
    base = stats["POSTHOG_BASE_URL"].rstrip("/")
    response = requests.request(
        kwargs.pop("method", "GET"),
        f"{base}/api/projects/{stats['POSTHOG_PROJECT_ID']}/{path}",
        headers={"Authorization": f"Bearer {stats['POSTHOG_PERSONAL_API_KEY']}"},
        timeout=TIMEOUT_SECONDS,
        **kwargs,
    )
    response.raise_for_status()
    return response.json()


def list_insights() -> list[tuple[str, str]]:
    """(short_id, name) of the saved insights, cached: this feeds a select."""

    def fetch():
        results = _api("insights/", params={"limit": 500, "saved": "true"})["results"]
        return sorted(
            (i["short_id"], i.get("name") or i.get("derived_name") or i["short_id"])
            for i in results
        )

    return cache.get_or_set("stats.posthog_insights", fetch, INSIGHTS_CACHE_SECONDS)


def run_insight(short_id: str) -> dict[date, float]:
    """Run the saved query of an insight, month by month.

    # ponytail: first series only; a breakdown or a formula insight needs
    # its own rule, say so in the KeyResult help text instead of guessing.
    """
    insights = _api("insights/", params={"short_id": short_id})["results"]
    if not insights:
        raise ValueError(f"Insight PostHog {short_id} introuvable")
    query = insights[0]["query"]
    query = query.get("source") or query  # InsightVizNode wraps the real query
    query = {**query, "interval": "month"}
    results = _api("query/", method="POST", json={"query": query}).get("results")
    if not results:
        raise ValueError(f"Insight PostHog {short_id} ne renvoie aucune donnée")
    first = results[0]
    return {
        parse_date(day).date(): float(value or 0)
        for day, value in zip(first.get("days") or [], first.get("data") or [])
    }


class InsightSelect(forms.Select):
    """A select listing the saved insights; empty when PostHog is unreachable
    so the form still opens."""

    def __init__(self, attrs=None, choices=()):
        try:
            choices = [("", "---------"), *list_insights()]
        except Exception:
            logger.exception("PostHog insights unavailable")
            choices = [("", "PostHog injoignable")]
        super().__init__(attrs, choices)
