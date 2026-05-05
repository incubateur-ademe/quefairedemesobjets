"""Minimal Model Context Protocol (MCP) server, JSON-RPC over HTTP POST.

Exposes the markdown docs as MCP resources and one prompt template that
guides an LLM through the recommended workflow. No tools (this is a
documentation-only server: the LLM calls BAN and ADEME directly using
its host's HTTP capability).

Spec: https://modelcontextprotocol.io/specification
Transport: a stripped-down Streamable HTTP — POST returns
`application/json`, never SSE, since we have no server-initiated messages.
"""

from __future__ import annotations

import json
from typing import Any

from django.http import HttpRequest, HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from . import docs as docs_module

SERVER_NAME = "qfdmo-llm-guide"
SERVER_VERSION = "0.1.0"
PROTOCOL_VERSION = "2024-11-05"

PROMPT_NAME = "find_circular_solution"
PROMPT_DESCRIPTION = (
    "Guide pas-à-pas pour aider un utilisateur à trouver, en France, où "
    "réparer / donner / acheter d'occasion / rapporter / trier un objet ou "
    "un déchet, en interrogeant l'API ADEME « Que Faire De Mes Objets et "
    "Déchets »."
)

PROMPT_TEMPLATE = """\
Tu es un assistant qui aide un utilisateur à trouver, **en France**, une
solution circulaire (réparer, donner, jeter, acheter d'occasion, louer…)
pour un objet ou un déchet.

Question de l'utilisateur :
{user_query}

{location_block}\
Marche à suivre obligatoire :

1. **Localisation**. Si la localisation n'est pas claire, demande à
   l'utilisateur son adresse, code postal ou ville. N'utilise jamais de
   coordonnées sans accord explicite.

2. **Sous-catégorie d'objet**. Identifie le code parmi la liste de la
   ressource MCP `qfdmo://sous-categories`. Si plusieurs sont plausibles,
   pose une question de clarification.

3. **Action**. Choisis le code parmi la liste de la ressource
   `qfdmo://actions` : preter, emprunter, louer, mettre en location,
   reparer, rapporter, donner, echanger, acheter, revendre, trier.

4. **Géocodage**. Appelle la BAN (cf. `qfdmo://geocoding`) :
   `https://api-adresse.data.gouv.fr/search/?q=<adresse>&limit=1`
   pour obtenir longitude et latitude.

5. **Recherche**. Appelle l'API ADEME (cf. `qfdmo://search-api`) :
   `https://data.ademe.fr/data-fair/api/v1/datasets/wvw1zecq4f4gyvonve5j0hr7/lines`
   avec :
   - `geo_distance=<lon>:<lat>:<rayon_metres>` (essayer 5000 m, élargir si vide)
   - `qs=<action>:"<sous_categorie>"`
   - `sort=_geo_distance`
   - `size=10`
   - `select=nom,adresse,code_postal,ville,horaires_description,site_web,latitude,
     longitude,paternite`

6. **Paternité**. Identifier les sources qui ont participées au référencement des
   acteurs récupérés lors de l'étape 5.
   - À part pour les sources `Que faire de mes objets et déchets` et `ADEME`,
     retrouver les sources qui ont participées au référencement de l'acteur via
     `qfdmo://sources` :
     - Récupérer l'`url` de chaque sources grâce à son `libelle`
   - Pour chaque source trouvée, ajouter le libellé et l'url au champ `paternite` de
   l'acteur.

7. **Restitution**. Présente jusqu'à 5 résultats classés par proximité, avec
   nom, adresse, distance approximative, horaires si présents, lien web si
   présent. Conclus toujours par : « Source : Que Faire De Mes Objets et
   Déchets / ADEME ».

8. **Si aucun résultat**, multiplie le rayon par 2 jusqu'à 50 km, puis
   redirige vers <https://quefairedemesdechets.ademe.fr> en cas d'échec.
"""


def _resource_descriptor(doc: docs_module.Doc) -> dict[str, Any]:
    return {
        "uri": doc.uri,
        "name": doc.title,
        "description": doc.description,
        "mimeType": "text/markdown",
    }


def _render_prompt(user_query: str, location_hint: str | None) -> str:
    location_block = ""
    if location_hint:
        location_block = f"Indication de localisation fournie : {location_hint}\n\n"
    return PROMPT_TEMPLATE.format(
        user_query=user_query.strip(),
        location_block=location_block,
    )


def _ok(req_id: Any, result: dict[str, Any]) -> dict[str, Any]:
    return {"jsonrpc": "2.0", "id": req_id, "result": result}


def _err(req_id: Any, code: int, message: str) -> dict[str, Any]:
    return {"jsonrpc": "2.0", "id": req_id, "error": {"code": code, "message": message}}


def _handle(message: dict[str, Any]) -> dict[str, Any] | None:
    """Process one JSON-RPC message. Returns None for notifications."""
    method = message.get("method")
    req_id = message.get("id")
    params = message.get("params") or {}
    is_notification = "id" not in message

    if method == "initialize":
        return _ok(
            req_id,
            {
                "protocolVersion": PROTOCOL_VERSION,
                "capabilities": {
                    "resources": {"subscribe": False, "listChanged": False},
                    "prompts": {"listChanged": False},
                    "tools": {"listChanged": False},
                },
                "serverInfo": {"name": SERVER_NAME, "version": SERVER_VERSION},
            },
        )

    if method in {"notifications/initialized", "notifications/cancelled"}:
        return None

    if is_notification:
        return None

    if method == "ping":
        return _ok(req_id, {})

    if method == "resources/list":
        return _ok(
            req_id,
            {"resources": [_resource_descriptor(d) for d in docs_module.DOCS]},
        )

    if method == "resources/read":
        uri = params.get("uri")
        doc = docs_module.DOCS_BY_URI.get(uri or "")
        if doc is None:
            return _err(req_id, -32602, f"Unknown resource URI: {uri!r}")
        return _ok(
            req_id,
            {
                "contents": [
                    {
                        "uri": doc.uri,
                        "mimeType": "text/markdown",
                        "text": docs_module.read(doc),
                    }
                ]
            },
        )

    if method == "prompts/list":
        return _ok(
            req_id,
            {
                "prompts": [
                    {
                        "name": PROMPT_NAME,
                        "description": PROMPT_DESCRIPTION,
                        "arguments": [
                            {
                                "name": "user_query",
                                "description": (
                                    "La question de l'utilisateur, telle qu'il l'a"
                                    " posée."
                                ),
                                "required": True,
                            },
                            {
                                "name": "location_hint",
                                "description": (
                                    "Indication de localisation déjà fournie"
                                    " (ville, code postal, adresse). Optionnel."
                                ),
                                "required": False,
                            },
                        ],
                    }
                ]
            },
        )

    if method == "prompts/get":
        if params.get("name") != PROMPT_NAME:
            return _err(req_id, -32602, f"Unknown prompt: {params.get('name')!r}")
        args = params.get("arguments") or {}
        user_query = args.get("user_query")
        if not user_query:
            return _err(req_id, -32602, "Missing required argument: user_query")
        location_hint = args.get("location_hint")
        return _ok(
            req_id,
            {
                "description": PROMPT_DESCRIPTION,
                "messages": [
                    {
                        "role": "user",
                        "content": {
                            "type": "text",
                            "text": _render_prompt(user_query, location_hint),
                        },
                    }
                ],
            },
        )

    if method == "tools/list":
        return _ok(req_id, {"tools": []})

    return _err(req_id, -32601, f"Method not found: {method}")


@csrf_exempt
@require_POST
def mcp_endpoint(request: HttpRequest) -> HttpResponse:
    try:
        payload = json.loads(request.body.decode("utf-8") or "{}")
    except (json.JSONDecodeError, UnicodeDecodeError):
        return JsonResponse(
            {
                "jsonrpc": "2.0",
                "id": None,
                "error": {"code": -32700, "message": "Parse error"},
            },
            status=400,
        )

    if isinstance(payload, list):
        responses = [r for r in (_handle(m) for m in payload) if r is not None]
        if not responses:
            return HttpResponse(status=202)
        return JsonResponse(responses, safe=False)

    response = _handle(payload)
    if response is None:
        return HttpResponse(status=202)
    return JsonResponse(response)
