"""Address suggestions, proxied from the BAN: one timeout, one cache, no
CORS coupling for the browser."""

import hashlib
import logging

import requests
from django.core.cache import cache

from qfdmo.views.autocomplete import BAN_API_URL, BAN_TIMEOUT_SECONDS

logger = logging.getLogger(__name__)

RESULTS_COUNT = 5
MIN_LENGTH = 3
MAX_LENGTH = 200
CACHE_TTL = 60 * 60 * 24

# BAN types designating a precise point rather than a municipality.
PRECISE_TYPES = frozenset({"housenumber", "street", "locality"})


def suggest_adresses(query: str) -> list[dict]:
    """Suggestions for a typed address; an empty list below three characters."""
    query = (query or "").strip()[:MAX_LENGTH]
    if len(query) < MIN_LENGTH:
        return []

    key = _cache_key(query)
    results = cache.get(key)
    if results is None:
        results = _search(query)
        # An empty list may be an outage: not cached.
        if results:
            cache.set(key, results, CACHE_TTL)
    return results


def _search(query: str) -> list[dict]:
    try:
        response = requests.get(
            BAN_API_URL,
            params={"q": query, "limit": RESULTS_COUNT},
            timeout=BAN_TIMEOUT_SECONDS,
        )
        response.raise_for_status()
        features = (response.json() or {}).get("features") or []
    except (requests.RequestException, ValueError) as error:
        logger.warning("BAN proxy failed: %s", error)
        return []

    suggestions = (_suggestion(feature) for feature in features)
    return [suggestion for suggestion in suggestions if suggestion]


def _suggestion(feature: dict) -> dict | None:
    """One suggestion, or None for an unusable feature. `precise` tells an
    address from a municipality, which has no position to show."""
    try:
        properties = feature["properties"]
        longitude, latitude = feature["geometry"]["coordinates"][:2]
    except (KeyError, IndexError, TypeError, ValueError):
        return None

    label = properties.get("label")
    if not label:
        return None

    return {
        "label": label,
        "detail": properties.get("context") or "",
        "longitude": longitude,
        "latitude": latitude,
        "precise": properties.get("type") in PRECISE_TYPES,
    }


def _cache_key(query: str) -> str:
    """A hashed key: cache backends refuse spaces and long keys."""
    digest = hashlib.sha256(query.casefold().encode()).hexdigest()[:32]
    return f"assistant:adresse:{digest}"
