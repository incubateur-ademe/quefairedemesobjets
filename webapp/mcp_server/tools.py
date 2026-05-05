"""MCP tools exposed to the client.

Each tool has:
- a JSON Schema describing its inputs (fed to `tools/list`),
- a handler that receives the validated arguments and returns a Python
  payload, which `server.py` wraps as MCP `content`.

Handlers raise `ToolError` on user-facing failures (bad arguments, upstream
errors). `UpstreamError` from `api_client` is mapped to `ToolError`.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any, Callable

from . import api_client, catalog


class ToolError(Exception):
    """User-facing error to be returned with `isError: true`."""


@dataclass(frozen=True)
class Tool:
    name: str
    title: str
    description: str
    input_schema: dict[str, Any]
    handler: Callable[[dict[str, Any]], Any]

    def descriptor(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "title": self.title,
            "description": self.description,
            "inputSchema": self.input_schema,
        }


# ---------- handlers ----------


def _geocode_handler(args: dict[str, Any]) -> dict[str, Any]:
    query = (args.get("query") or "").strip()
    if not query:
        raise ToolError("`query` is required and must not be empty.")
    limit = int(args.get("limit") or 1)
    limit = max(1, min(limit, 10))
    try:
        features = api_client.geocode(query, limit=limit)
    except api_client.UpstreamError as exc:
        raise ToolError(str(exc)) from exc
    if not features:
        return {"query": query, "results": []}
    results = []
    for feat in features:
        coords = (feat.get("geometry") or {}).get("coordinates") or [None, None]
        props = feat.get("properties") or {}
        results.append(
            {
                "longitude": coords[0],
                "latitude": coords[1],
                "label": props.get("label"),
                "score": props.get("score"),
                "city": props.get("city"),
                "postcode": props.get("postcode"),
                "type": props.get("type"),
            }
        )
    return {"query": query, "results": results}


def _list_actions_handler(args: dict[str, Any]) -> dict[str, Any]:
    query = args.get("query")
    actions = catalog.filter_actions(query)
    return {
        "actions": [
            {"code": a.code, "libelle": a.libelle, "description": a.description}
            for a in actions
        ]
    }


def _list_sous_categories_handler(args: dict[str, Any]) -> dict[str, Any]:
    query = args.get("query")
    items = catalog.filter_sous_categories(query)
    return {
        "sous_categories": [
            {"code": sc.code, "libelle": sc.libelle, "groupe": sc.groupe}
            for sc in items
        ]
    }


def _list_sources_handler(args: dict[str, Any]) -> dict[str, Any]:
    """List Source entries from the local Django model.

    Used to enrich the `paternite` field of returned actors with a clickable
    URL per source libellé.
    """
    from qfdmo.models import Source  # local import to avoid app-loading cycles

    queryset = Source.objects.filter(afficher=True).order_by("libelle")
    libelle_contains = (args.get("libelle_contains") or "").strip()
    if libelle_contains:
        queryset = queryset.filter(libelle__icontains=libelle_contains)
    return {
        "sources": [
            {"code": s.code, "libelle": s.libelle, "url": s.url or None}
            for s in queryset
        ]
    }


_EARTH_RADIUS_M = 6_371_000.0


def _haversine_m(lon1: float, lat1: float, lon2: float, lat2: float) -> float:
    rlat1, rlat2 = math.radians(lat1), math.radians(lat2)
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(rlat1) * math.cos(rlat2) * math.sin(dlon / 2) ** 2
    )
    return 2 * _EARTH_RADIUS_M * math.asin(math.sqrt(a))


def _validate_coords(args: dict[str, Any]) -> tuple[float, float]:
    try:
        lon = float(args["longitude"])
        lat = float(args["latitude"])
    except (KeyError, TypeError, ValueError) as exc:
        raise ToolError("`longitude` and `latitude` must be numbers.") from exc
    if not -180 <= lon <= 180 or not -90 <= lat <= 90:
        raise ToolError("`longitude`/`latitude` are out of valid bounds.")
    return lon, lat


def _validate_action_and_subcat(args: dict[str, Any]) -> tuple[str, str]:
    action = (args.get("action") or "").strip()
    sous_cat = (args.get("sous_categorie") or "").strip()
    if action not in catalog.ACTIONS_BY_CODE:
        raise ToolError(
            f"Unknown action {action!r}. Call `list_actions` to discover valid codes."
        )
    if sous_cat not in catalog.SOUS_CATEGORIES_BY_CODE:
        raise ToolError(
            f"Unknown sous_categorie {sous_cat!r}. "
            "Call `list_sous_categories` to discover valid codes."
        )
    return action, sous_cat


def _format_actor(actor: dict[str, Any], origin: tuple[float, float]) -> dict[str, Any]:
    lon = actor.get("longitude")
    lat = actor.get("latitude")
    distance_m: int | None = None
    upstream_distance = actor.get("_geo_distance")
    if isinstance(upstream_distance, (int, float)):
        distance_m = round(upstream_distance)
    elif isinstance(lon, (int, float)) and isinstance(lat, (int, float)):
        distance_m = round(_haversine_m(origin[0], origin[1], lon, lat))
    return {
        "nom": actor.get("nom"),
        "adresse": actor.get("adresse"),
        "code_postal": actor.get("code_postal"),
        "ville": actor.get("ville"),
        "latitude": lat,
        "longitude": lon,
        "horaires_description": actor.get("horaires_description"),
        "site_web": actor.get("site_web"),
        "telephone": actor.get("telephone"),
        "paternite": actor.get("paternite"),
        "distance_m": distance_m,
    }


def _search_actors_handler(args: dict[str, Any]) -> dict[str, Any]:
    lon, lat = _validate_coords(args)
    action, sous_cat = _validate_action_and_subcat(args)
    radius = int(args.get("radius_meters") or 5000)
    radius = max(100, min(radius, 100_000))
    size = int(args.get("size") or 10)
    size = max(1, min(size, 20))
    try:
        body = api_client.search_actors(
            longitude=lon,
            latitude=lat,
            radius_meters=radius,
            action=action,
            sous_categorie=sous_cat,
            size=size,
        )
    except api_client.UpstreamError as exc:
        raise ToolError(str(exc)) from exc
    actors = [_format_actor(a, (lon, lat)) for a in body.get("results") or []]
    return {
        "total": body.get("total", len(actors)),
        "radius_meters": radius,
        "action": action,
        "sous_categorie": sous_cat,
        "actors": actors,
    }


def _find_circular_solution_handler(args: dict[str, Any]) -> dict[str, Any]:
    address = (args.get("address") or "").strip()
    if not address:
        raise ToolError("`address` is required.")
    action, sous_cat = _validate_action_and_subcat(args)
    initial_radius = int(args.get("radius_meters") or 5000)
    initial_radius = max(100, min(initial_radius, 50_000))
    size = int(args.get("size") or 10)
    size = max(1, min(size, 20))

    geo = _geocode_handler({"query": address, "limit": 1})
    if not geo["results"]:
        return {
            "address": address,
            "location": None,
            "actors": [],
            "message": "Address could not be geocoded by BAN.",
        }
    location = geo["results"][0]
    lon = location["longitude"]
    lat = location["latitude"]

    radius = initial_radius
    attempts: list[dict[str, Any]] = []
    while radius <= 50_000:
        body = _search_actors_handler(
            {
                "longitude": lon,
                "latitude": lat,
                "action": action,
                "sous_categorie": sous_cat,
                "radius_meters": radius,
                "size": size,
            }
        )
        attempts.append({"radius_meters": radius, "found": len(body["actors"])})
        if body["actors"]:
            return {
                "address": address,
                "location": location,
                "action": action,
                "sous_categorie": sous_cat,
                "radius_meters": radius,
                "attempts": attempts,
                "actors": body["actors"],
            }
        if radius >= 50_000:
            break
        radius = min(radius * 2, 50_000)

    return {
        "address": address,
        "location": location,
        "action": action,
        "sous_categorie": sous_cat,
        "radius_meters": radius,
        "attempts": attempts,
        "actors": [],
        "message": (
            "No actor found within 50km. Suggest the user visit "
            "https://quefairedemesdechets.ademe.fr"
        ),
    }


# ---------- tool registry ----------


_ACTION_CODES = [a.code for a in catalog.ACTIONS]


TOOLS: tuple[Tool, ...] = (
    Tool(
        name="geocode_address",
        title="Géocoder une adresse française",
        description=(
            "Convertit une adresse, une ville ou un code postal français en "
            "coordonnées (longitude, latitude) via la Base Adresse Nationale. "
            "À utiliser avant `search_actors` pour obtenir les coordonnées."
        ),
        input_schema={
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": (
                        "Adresse libre, ville ou code postal (ex. "
                        "'10 rue de Rivoli Paris', 'Lyon 3', '75011')."
                    ),
                },
                "limit": {
                    "type": "integer",
                    "minimum": 1,
                    "maximum": 10,
                    "default": 1,
                    "description": "Nombre maximum de résultats à renvoyer.",
                },
            },
            "required": ["query"],
            "additionalProperties": False,
        },
        handler=_geocode_handler,
    ),
    Tool(
        name="list_actions",
        title="Lister les actions de l'économie circulaire",
        description=(
            "Renvoie les codes d'action acceptés par `search_actors`. "
            "Couvre **tous les gestes circulaires**, pas seulement le tri : "
            "`reparer` (faire réparer), `donner`, `acheter` (acheter "
            "d'occasion), `revendre`, `louer`, `mettreenlocation`, "
            "`emprunter`, `preter`, `echanger`, `rapporter` (déposer en fin "
            "de vie), `trier`. Optionnellement filtrable par mot-clé."
        ),
        input_schema={
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": (
                        "Mot-clé pour filtrer (ex. 'reparer', 'don', 'achat')."
                    ),
                }
            },
            "additionalProperties": False,
        },
        handler=_list_actions_handler,
    ),
    Tool(
        name="list_sous_categories",
        title="Lister les sous-catégories d'objet",
        description=(
            "Renvoie les codes de sous-catégorie d'objet acceptés par "
            "`search_actors`. Couvre **tous types d'objets et de déchets** : "
            "électronique (smartphone, ordinateur, électroménager), mobilité "
            "(velo, trottinette), textile (vetement, chaussure), meuble, "
            "jouet, livre, outil, instrument de musique, vaisselle, "
            "peinture, pile, ampoule, médicament, etc. Optionnellement "
            "filtrable par mot-clé."
        ),
        input_schema={
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": (
                        "Mot-clé pour filtrer (ex. 'velo', 'meuble', " "'peinture')."
                    ),
                }
            },
            "additionalProperties": False,
        },
        handler=_list_sous_categories_handler,
    ),
    Tool(
        name="list_sources",
        title="Lister les sources contributrices",
        description=(
            "Renvoie les sources qui contribuent au référencement des acteurs "
            "(libellé, code, URL). Sert à enrichir le champ `paternite` des "
            "acteurs renvoyés par `search_actors` en associant un lien à "
            "chaque libellé de source."
        ),
        input_schema={
            "type": "object",
            "properties": {
                "libelle_contains": {
                    "type": "string",
                    "description": (
                        "Filtre par sous-chaîne du libellé (ex. 'CRAR', "
                        "'Eco-systèmes')."
                    ),
                }
            },
            "additionalProperties": False,
        },
        handler=_list_sources_handler,
    ),
    Tool(
        name="search_actors",
        title="Rechercher des acteurs de l'économie circulaire",
        description=(
            "Recherche dans l'annuaire officiel ADEME (~380 000 acteurs en "
            "France) les **réparateurs, ressourceries, recycleries, "
            "friperies, repair cafés, boutiques de seconde main, "
            "magasins de location, points de collecte, déchèteries, "
            "associations** qui proposent une action donnée (réparer, "
            "donner, acheter d'occasion, louer, emprunter, échanger, "
            "rapporter, trier…) pour une sous-catégorie d'objet (téléphone, "
            "vélo, vêtement, électroménager, meuble, etc.), dans un rayon "
            "autour d'un point géographique. Trie par distance croissante. "
            "Pour partir d'une adresse plutôt que de coordonnées, utiliser "
            "`find_circular_solution`."
        ),
        input_schema={
            "type": "object",
            "properties": {
                "longitude": {
                    "type": "number",
                    "description": "Longitude du point de recherche.",
                },
                "latitude": {
                    "type": "number",
                    "description": "Latitude du point de recherche.",
                },
                "action": {
                    "type": "string",
                    "enum": _ACTION_CODES,
                    "description": (
                        "Code d'action — voir `list_actions` (ex. 'reparer', "
                        "'donner', 'rapporter')."
                    ),
                },
                "sous_categorie": {
                    "type": "string",
                    "description": (
                        "Code de sous-catégorie d'objet — voir "
                        "`list_sous_categories` (ex. 'velo', 'vetement')."
                    ),
                },
                "radius_meters": {
                    "type": "integer",
                    "minimum": 100,
                    "maximum": 100000,
                    "default": 5000,
                    "description": "Rayon de recherche en mètres.",
                },
                "size": {
                    "type": "integer",
                    "minimum": 1,
                    "maximum": 20,
                    "default": 10,
                    "description": "Nombre maximum d'acteurs renvoyés.",
                },
            },
            "required": ["longitude", "latitude", "action", "sous_categorie"],
            "additionalProperties": False,
        },
        handler=_search_actors_handler,
    ),
    Tool(
        name="find_circular_solution",
        title="Trouver une solution circulaire (geocode + recherche)",
        description=(
            "**Point d'entrée principal** pour répondre à toute question "
            "du type « où **réparer / donner / vendre / acheter d'occasion / "
            "louer / emprunter / échanger / rapporter / trier** [un objet] "
            "près de [lieu] ? » en France. Couvre tous les objets "
            "(téléphone, ordinateur, vélo, électroménager, vêtement, meuble, "
            "jouet, outil, livre…) et tous les déchets — pas seulement les "
            "déchèteries : aussi réparateurs, repair cafés, ressourceries, "
            "recycleries, friperies, boutiques de seconde main, locations, "
            "associations, points de collecte. Tool composé : géocode "
            "l'adresse via la BAN, puis interroge l'annuaire ADEME ; en cas "
            "de zéro résultat, élargit automatiquement le rayon (×2) jusqu'à "
            "50 km. À privilégier en un seul appel."
        ),
        input_schema={
            "type": "object",
            "properties": {
                "address": {
                    "type": "string",
                    "description": ("Adresse, ville ou code postal de l'utilisateur."),
                },
                "action": {
                    "type": "string",
                    "enum": _ACTION_CODES,
                    "description": "Code d'action — voir `list_actions`.",
                },
                "sous_categorie": {
                    "type": "string",
                    "description": (
                        "Code de sous-catégorie — voir `list_sous_categories`."
                    ),
                },
                "radius_meters": {
                    "type": "integer",
                    "minimum": 100,
                    "maximum": 50000,
                    "default": 5000,
                    "description": "Rayon initial (élargi automatiquement).",
                },
                "size": {
                    "type": "integer",
                    "minimum": 1,
                    "maximum": 20,
                    "default": 10,
                    "description": "Nombre maximum d'acteurs renvoyés.",
                },
            },
            "required": ["address", "action", "sous_categorie"],
            "additionalProperties": False,
        },
        handler=_find_circular_solution_handler,
    ),
)

TOOLS_BY_NAME: dict[str, Tool] = {t.name: t for t in TOOLS}
