"""Address suggestions for the assistant, proxying the BAN.

The browser never talks to the BAN directly: a single timeout, a single cache
policy, and no CORS coupling. Served by `/api/v1/adresses`.

The "Autour de moi" option of the legacy view is not carried over:
geolocation is out of the MVP scope (#3295).
"""

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

# The BAN types that designate a precise point, as opposed to a municipality.
PRECISE_TYPES = frozenset({"housenumber", "street", "locality"})


def suggest_adresses(query: str) -> list[dict]:
    """Suggestions for a typed address, or an empty list below three characters.

    The BAN answers in ~200 ms, far beyond the 50 ms budget, and it dominates:
    the proxy adds nothing measurable. The same addresses are typed again and
    again, so a shared cache brings repeated requests under a millisecond. The
    address registry moves slowly: 24 h is safe.
    """
    query = (query or "").strip()[:MAX_LENGTH]
    if len(query) < MIN_LENGTH:
        return []

    key = _cache_key(query)
    results = cache.get(key)
    if results is None:
        results = _search(query)
        # A BAN failure returns an empty list: do not remember it, or a
        # passing outage would freeze for 24 h.
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
        logger.warning("BAN proxy failed for %r: %s", query, error)
        return []

    suggestions = (_suggestion(feature) for feature in features)
    return [suggestion for suggestion in suggestions if suggestion]


def _suggestion(feature: dict) -> dict | None:
    """One suggestion, or None if the BAN returns an unusable feature.

    `precise` tells an address from a municipality: the red marker only
    shows for the former. "Lyon" has no position to show (#3356), and its
    geographic center would mislead the user.
    """
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
    """Stable, space-free key for a free-text input.

    Memcached refuses spaces and control characters, which an address always
    contains: the input is hashed rather than copied. Case folding groups
    "Auray" and "auray" on the same entry.
    """
    digest = hashlib.sha256(query.casefold().encode()).hexdigest()[:32]
    return f"assistant:adresse:{digest}"
