"""Minimal Model Context Protocol (MCP) server, JSON-RPC over HTTP POST.

Exposes:
- **tools** — the primary interface; thin proxies over BAN and ADEME data-fair
  (see `tools.py`).
- **resources** — markdown docs for hosts that surface them (see `docs.py`).
- **prompts** — a single workflow prompt that drives an LLM through the tools.

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
from . import tools as tools_module

SERVER_NAME = "qfdmo-llm-guide"
SERVER_VERSION = "0.2.0"
PROTOCOL_VERSION = "2024-11-05"

PROMPT_NAME = "find_circular_solution"
PROMPT_DESCRIPTION = (
    "Guide pas-à-pas pour aider un utilisateur à trouver, en France, où "
    "réparer / donner / acheter d'occasion / rapporter / trier un objet ou "
    "un déchet, en s'appuyant sur les tools MCP de ce serveur."
)

PROMPT_TEMPLATE = """\
Tu es un assistant qui aide un utilisateur à trouver, **en France**, une
solution circulaire (réparer, donner, jeter, acheter d'occasion, louer…)
pour un objet ou un déchet, en utilisant **uniquement les tools MCP** de
ce serveur (n'appelle jamais directement une URL HTTP, n'invente aucune
donnée).

Question de l'utilisateur :
{user_query}

{location_block}\
Marche à suivre :

1. **Localisation**. Si la localisation n'est pas claire, demande à
   l'utilisateur son adresse, code postal ou ville. N'utilise jamais de
   coordonnées sans accord explicite.

2. **Sous-catégorie d'objet**. Appelle le tool `list_sous_categories` (avec
   un mot-clé issu de la question, ex. `"velo"`) pour identifier le code à
   utiliser. Si plusieurs codes sont plausibles, pose une question de
   clarification.

3. **Action**. Appelle `list_actions` (avec un mot-clé issu de l'intention
   de l'utilisateur, ex. `"reparer"`) pour choisir un code parmi : preter,
   emprunter, louer, mettreenlocation, reparer, rapporter, donner, echanger,
   acheter, revendre, trier.

4. **Recherche**. Appelle le tool composé
   `find_circular_solution(address, action, sous_categorie)`. Il géocode
   l'adresse via la BAN, interroge l'API ADEME, et élargit automatiquement
   le rayon (×2 jusqu'à 50 km) si zéro résultat.
   - Alternativement, si tu as déjà des coordonnées, utilise
     `geocode_address` puis `search_actors` séparément.

5. **Paternité**. Pour chaque acteur renvoyé, le champ `paternite` liste
   des libellés de sources contributrices (séparés par `|`).
   - Pour chaque libellé **autre que** « Que faire de mes objets et déchets »
     et « ADEME », appelle `list_sources(libelle_contains=<libelle>)` pour
     récupérer son URL et l'ajouter à la restitution.

6. **Restitution**. Présente jusqu'à 5 acteurs classés par proximité, avec
   nom, adresse, distance approximative (champ `distance_m`), horaires si
   présents, lien web si présent, et la liste des sources avec leurs URLs.
   Conclus toujours par : « Source : Que Faire De Mes Objets et
   Déchets / ADEME ».

7. **Si aucun résultat**, le tool a déjà élargi jusqu'à 50 km : redirige
   l'utilisateur vers <https://quefairedemesdechets.ademe.fr>.
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


def _tool_text_result(payload: Any, *, is_error: bool = False) -> dict[str, Any]:
    text = (
        payload
        if isinstance(payload, str)
        else json.dumps(payload, ensure_ascii=False, indent=2)
    )
    return {
        "content": [{"type": "text", "text": text}],
        "isError": is_error,
    }


def _handle_tools_call(req_id: Any, params: dict[str, Any]) -> dict[str, Any]:
    name = params.get("name")
    tool = tools_module.TOOLS_BY_NAME.get(name or "")
    if tool is None:
        return _err(req_id, -32602, f"Unknown tool: {name!r}")
    arguments = params.get("arguments") or {}
    if not isinstance(arguments, dict):
        return _err(req_id, -32602, "`arguments` must be an object")
    try:
        result = tool.handler(arguments)
    except tools_module.ToolError as exc:
        return _ok(req_id, _tool_text_result(str(exc), is_error=True))
    except Exception as exc:  # noqa: BLE001 — surface unexpected errors to client
        return _ok(
            req_id,
            _tool_text_result(f"Internal tool error: {exc}", is_error=True),
        )
    return _ok(req_id, _tool_text_result(result))


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
                    "tools": {"listChanged": False},
                    "resources": {"subscribe": False, "listChanged": False},
                    "prompts": {"listChanged": False},
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

    if method == "tools/list":
        return _ok(
            req_id,
            {"tools": [t.descriptor() for t in tools_module.TOOLS]},
        )

    if method == "tools/call":
        return _handle_tools_call(req_id, params)

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
