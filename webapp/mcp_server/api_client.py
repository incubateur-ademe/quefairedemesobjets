"""HTTP proxies to the public APIs the MCP tools rely on.

- BAN (Base Adresse Nationale) — geocoding.
- ADEME data-fair — actors of the « Que Faire De Mes Objets et Déchets »
  dataset.

Both APIs are public, free, and require no key. We keep timeouts short so a
slow upstream cannot stall an MCP client.
"""

from __future__ import annotations

from typing import Any

import requests

BAN_SEARCH_URL = "https://api-adresse.data.gouv.fr/search/"
ADEME_DATASET_ID = "wvw1zecq4f4gyvonve5j0hr7"  # pragma allowlist secret
ADEME_LINES_URL = (
    "https://data.ademe.fr/data-fair/api/v1/datasets/" f"{ADEME_DATASET_ID}/lines"
)

DEFAULT_TIMEOUT = 10


class UpstreamError(RuntimeError):
    """Raised when an upstream API returns an error or an unparseable body."""


def geocode(query: str, *, limit: int = 1) -> list[dict[str, Any]]:
    """Return BAN features for the address query, best match first.

    Each feature exposes `geometry.coordinates = [longitude, latitude]` and a
    `properties` dict with `label`, `score`, `city`, `postcode`, `type`…
    """
    response = requests.get(
        BAN_SEARCH_URL,
        params={"q": query, "limit": limit},
        timeout=DEFAULT_TIMEOUT,
    )
    if not response.ok:
        raise UpstreamError(
            f"BAN returned HTTP {response.status_code} for query {query!r}"
        )
    try:
        body = response.json()
    except ValueError as exc:
        raise UpstreamError(f"BAN returned non-JSON body: {exc}") from exc
    return list(body.get("features") or [])


def search_actors(
    *,
    longitude: float,
    latitude: float,
    radius_meters: int,
    action: str,
    sous_categorie: str,
    size: int = 10,
    select: list[str] | None = None,
) -> dict[str, Any]:
    """Query ADEME data-fair `/lines` and return its JSON body verbatim.

    Filters on geo distance and on a full-text match of (action, sous_categorie)
    inside the `propositions_de_services` JSON column. The dataset does not
    expose `reparer` / `donner` / … as exact-filterable fields, and does not
    allow sorting on `_geo_distance`, but a `geo_distance` query already
    returns rows ordered by ascending distance.
    """
    select = select or [
        "nom",
        "adresse",
        "code_postal",
        "ville",
        "horaires_description",
        "site_web",
        "telephone",
        "latitude",
        "longitude",
        "paternite",
    ]
    params = {
        "geo_distance": f"{longitude}:{latitude}:{radius_meters}",
        "q": sous_categorie,
        "q_mode": "complete",
        "q_fields": action,
        "size": size,
        "select": ",".join(select),
    }
    response = requests.get(ADEME_LINES_URL, params=params, timeout=DEFAULT_TIMEOUT)
    if not response.ok:
        raise UpstreamError(f"ADEME data-fair returned HTTP {response.status_code}")
    try:
        return response.json()
    except ValueError as exc:
        raise UpstreamError(f"ADEME data-fair returned non-JSON body: {exc}") from exc
