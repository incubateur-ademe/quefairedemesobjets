import json
from types import SimpleNamespace

import pytest

from mcp_server import api_client, docs as docs_module, tools as tools_module
from mcp_server.server import PROMPT_NAME, PROTOCOL_VERSION, SERVER_NAME

MCP_URL = "/mcp"


def _rpc(client, method, params=None, req_id=1):
    body = {"jsonrpc": "2.0", "id": req_id, "method": method}
    if params is not None:
        body["params"] = params
    response = client.post(
        MCP_URL, data=json.dumps(body), content_type="application/json"
    )
    return response


def _fake_response(json_body, status_code=200):
    return SimpleNamespace(
        ok=200 <= status_code < 300,
        status_code=status_code,
        json=lambda: json_body,
    )


@pytest.mark.django_db
class TestInitialize:
    def test_returns_server_info_and_capabilities(self, client):
        response = _rpc(
            client,
            "initialize",
            {
                "protocolVersion": PROTOCOL_VERSION,
                "capabilities": {},
                "clientInfo": {"name": "test", "version": "0"},
            },
        )
        assert response.status_code == 200
        body = response.json()
        assert body["jsonrpc"] == "2.0"
        assert body["id"] == 1
        assert body["result"]["protocolVersion"] == PROTOCOL_VERSION
        assert body["result"]["serverInfo"]["name"] == SERVER_NAME
        caps = body["result"]["capabilities"]
        assert "tools" in caps
        assert "resources" in caps
        assert "prompts" in caps


@pytest.mark.django_db
class TestNotification:
    def test_initialized_notification_returns_202(self, client):
        body = {"jsonrpc": "2.0", "method": "notifications/initialized"}
        response = client.post(
            MCP_URL, data=json.dumps(body), content_type="application/json"
        )
        assert response.status_code == 202


@pytest.mark.django_db
class TestResources:
    def test_list_returns_all_docs(self, client):
        body = _rpc(client, "resources/list").json()
        uris = {r["uri"] for r in body["result"]["resources"]}
        assert uris == {d.uri for d in docs_module.DOCS}

    def test_read_returns_markdown_content(self, client):
        target = docs_module.DOCS_BY_SLUG["actions"]
        body = _rpc(client, "resources/read", {"uri": target.uri}).json()
        contents = body["result"]["contents"]
        assert len(contents) == 1
        assert contents[0]["uri"] == target.uri
        assert contents[0]["mimeType"] == "text/markdown"
        assert contents[0]["text"] == docs_module.read(target)

    def test_read_unknown_uri_returns_error(self, client):
        body = _rpc(client, "resources/read", {"uri": "qfdmo://does-not-exist"}).json()
        assert "error" in body
        assert body["error"]["code"] == -32602


@pytest.mark.django_db
class TestPrompts:
    def test_list_returns_one_prompt(self, client):
        body = _rpc(client, "prompts/list").json()
        prompts = body["result"]["prompts"]
        assert len(prompts) == 1
        assert prompts[0]["name"] == PROMPT_NAME
        names = {a["name"] for a in prompts[0]["arguments"]}
        assert names == {"user_query", "location_hint"}

    def test_get_renders_prompt_with_user_query(self, client):
        body = _rpc(
            client,
            "prompts/get",
            {
                "name": PROMPT_NAME,
                "arguments": {"user_query": "Où réparer mon téléphone à Paris ?"},
            },
        ).json()
        messages = body["result"]["messages"]
        assert len(messages) == 1
        text = messages[0]["content"]["text"]
        assert "Où réparer mon téléphone à Paris ?" in text
        assert "Indication de localisation fournie" not in text
        # The new prompt should refer to tools, not raw HTTP URLs.
        assert "find_circular_solution" in text
        assert "list_sous_categories" in text
        assert "data.ademe.fr" not in text

    def test_get_includes_location_hint_when_provided(self, client):
        body = _rpc(
            client,
            "prompts/get",
            {
                "name": PROMPT_NAME,
                "arguments": {
                    "user_query": "Donner des vêtements",
                    "location_hint": "Lyon 3e",
                },
            },
        ).json()
        text = body["result"]["messages"][0]["content"]["text"]
        assert "Lyon 3e" in text
        assert "Indication de localisation fournie" in text

    def test_get_missing_user_query_returns_error(self, client):
        body = _rpc(
            client, "prompts/get", {"name": PROMPT_NAME, "arguments": {}}
        ).json()
        assert "error" in body

    def test_get_unknown_prompt_returns_error(self, client):
        body = _rpc(
            client, "prompts/get", {"name": "nope", "arguments": {"user_query": "x"}}
        ).json()
        assert "error" in body


@pytest.mark.django_db
class TestToolsList:
    def test_list_exposes_all_tools(self, client):
        body = _rpc(client, "tools/list").json()
        names = {t["name"] for t in body["result"]["tools"]}
        assert names == {t.name for t in tools_module.TOOLS}

    def test_each_tool_has_name_description_and_input_schema(self, client):
        body = _rpc(client, "tools/list").json()
        for tool in body["result"]["tools"]:
            assert tool["name"]
            assert tool["description"]
            assert tool["inputSchema"]["type"] == "object"


def _call(client, name, arguments):
    return _rpc(client, "tools/call", {"name": name, "arguments": arguments}).json()


def _result_payload(body):
    """Decode the JSON text content emitted by a successful tool call."""
    return json.loads(body["result"]["content"][0]["text"])


@pytest.mark.django_db
class TestToolsCallErrors:
    def test_unknown_tool_returns_jsonrpc_error(self, client):
        body = _call(client, "no_such_tool", {})
        assert "error" in body
        assert body["error"]["code"] == -32602

    def test_tool_error_returns_isError_true(self, client):
        body = _call(client, "geocode_address", {"query": ""})
        assert body["result"]["isError"] is True
        assert "query" in body["result"]["content"][0]["text"]


@pytest.mark.django_db
class TestGeocodeAddressTool:
    def test_returns_first_feature(self, client, monkeypatch):
        feature = {
            "geometry": {"coordinates": [2.355097, 48.857074]},
            "properties": {
                "label": "10 Rue de Rivoli 75004 Paris",
                "score": 0.97,
                "city": "Paris",
                "postcode": "75004",
                "type": "housenumber",
            },
        }
        monkeypatch.setattr(
            api_client.requests,
            "get",
            lambda *a, **kw: _fake_response({"features": [feature]}),
        )
        body = _call(client, "geocode_address", {"query": "10 rue de rivoli paris"})
        payload = _result_payload(body)
        assert payload["query"] == "10 rue de rivoli paris"
        assert len(payload["results"]) == 1
        result = payload["results"][0]
        assert result["longitude"] == 2.355097
        assert result["latitude"] == 48.857074
        assert result["postcode"] == "75004"

    def test_no_features_returns_empty_results(self, client, monkeypatch):
        monkeypatch.setattr(
            api_client.requests,
            "get",
            lambda *a, **kw: _fake_response({"features": []}),
        )
        body = _call(client, "geocode_address", {"query": "lkjsdflkjsdf"})
        payload = _result_payload(body)
        assert payload["results"] == []

    def test_upstream_error_returns_tool_error(self, client, monkeypatch):
        monkeypatch.setattr(
            api_client.requests,
            "get",
            lambda *a, **kw: _fake_response({}, status_code=502),
        )
        body = _call(client, "geocode_address", {"query": "Paris"})
        assert body["result"]["isError"] is True


@pytest.mark.django_db
class TestListActionsTool:
    def test_unfiltered_returns_all(self, client):
        body = _call(client, "list_actions", {})
        codes = {a["code"] for a in _result_payload(body)["actions"]}
        assert "reparer" in codes
        assert "donner" in codes
        assert "mettreenlocation" in codes

    def test_filtered_by_keyword(self, client):
        body = _call(client, "list_actions", {"query": "rep"})
        codes = {a["code"] for a in _result_payload(body)["actions"]}
        assert "reparer" in codes


@pytest.mark.django_db
class TestListSousCategoriesTool:
    def test_unfiltered_returns_all(self, client):
        body = _call(client, "list_sous_categories", {})
        codes = {sc["code"] for sc in _result_payload(body)["sous_categories"]}
        assert "velo" in codes
        assert "vetement" in codes

    def test_filter_keyword(self, client):
        body = _call(client, "list_sous_categories", {"query": "peinture"})
        codes = [sc["code"] for sc in _result_payload(body)["sous_categories"]]
        assert any("peintures" in c for c in codes)


@pytest.mark.django_db
class TestListSourcesTool:
    def test_returns_visible_sources(self, client):
        from qfdmo.models import Source

        Source.objects.create(
            code="s1",
            libelle="CRAR Normandie",
            url="https://crar-normandie.fr/",
            afficher=True,
        )
        Source.objects.create(
            code="s2",
            libelle="Hidden Source",
            url="https://hidden.example",
            afficher=False,
        )
        body = _call(client, "list_sources", {})
        libelles = {s["libelle"] for s in _result_payload(body)["sources"]}
        assert "CRAR Normandie" in libelles
        assert "Hidden Source" not in libelles

    def test_filter_libelle_contains(self, client):
        from qfdmo.models import Source

        Source.objects.create(code="a1", libelle="CRAR Normandie", url="http://a")
        Source.objects.create(code="a2", libelle="Eco-systèmes", url="http://b")
        body = _call(client, "list_sources", {"libelle_contains": "CRAR"})
        sources = _result_payload(body)["sources"]
        assert len(sources) == 1
        assert sources[0]["libelle"] == "CRAR Normandie"


@pytest.mark.django_db
class TestSearchActorsTool:
    def _ademe_response(self):
        return {
            "total": 1,
            "results": [
                {
                    "nom": "Repair Café Test",
                    "adresse": "1 rue test",
                    "code_postal": "75001",
                    "ville": "Paris",
                    "horaires_description": "samedi matin",
                    "site_web": "https://example.org",
                    "telephone": None,
                    "latitude": 48.86,
                    "longitude": 2.35,
                    "paternite": "Que faire de mes objets et déchets | ADEME",
                }
            ],
        }

    def test_returns_actors_with_distance(self, client, monkeypatch):
        monkeypatch.setattr(
            api_client.requests,
            "get",
            lambda *a, **kw: _fake_response(self._ademe_response()),
        )
        body = _call(
            client,
            "search_actors",
            {
                "longitude": 2.3522,
                "latitude": 48.8566,
                "action": "reparer",
                "sous_categorie": "smartphone_tablette_et_console",
            },
        )
        payload = _result_payload(body)
        assert payload["total"] == 1
        assert len(payload["actors"]) == 1
        assert payload["actors"][0]["nom"] == "Repair Café Test"
        assert isinstance(payload["actors"][0]["distance_m"], int)

    def test_unknown_action_is_rejected(self, client):
        body = _call(
            client,
            "search_actors",
            {
                "longitude": 2.0,
                "latitude": 48.0,
                "action": "not_a_real_action",
                "sous_categorie": "velo",
            },
        )
        assert body["result"]["isError"] is True

    def test_unknown_sous_categorie_is_rejected(self, client):
        body = _call(
            client,
            "search_actors",
            {
                "longitude": 2.0,
                "latitude": 48.0,
                "action": "reparer",
                "sous_categorie": "not_a_real_subcat",
            },
        )
        assert body["result"]["isError"] is True


@pytest.mark.django_db
class TestFindCircularSolutionTool:
    def _ban_feature(self, lon=2.3522, lat=48.8566):
        return {
            "geometry": {"coordinates": [lon, lat]},
            "properties": {
                "label": "Paris",
                "score": 0.95,
                "city": "Paris",
                "postcode": "75001",
                "type": "municipality",
            },
        }

    def _make_get(self, ban_features, ademe_results_per_call):
        """Build a fake `requests.get` that returns BAN, then ADEME, then ADEME…"""
        calls = {"n": 0}

        def fake_get(url, *a, **kw):
            calls["n"] += 1
            if "api-adresse.data.gouv.fr" in url:
                return _fake_response({"features": ban_features})
            # ADEME data-fair: pop next configured result
            results = ademe_results_per_call.pop(0)
            return _fake_response({"total": len(results), "results": results})

        return fake_get

    def test_first_attempt_finds_actors(self, client, monkeypatch):
        actor = {
            "nom": "X",
            "adresse": "1",
            "code_postal": "75001",
            "ville": "Paris",
            "latitude": 48.86,
            "longitude": 2.35,
            "paternite": "ADEME",
        }
        monkeypatch.setattr(
            api_client.requests,
            "get",
            self._make_get([self._ban_feature()], [[actor]]),
        )
        body = _call(
            client,
            "find_circular_solution",
            {
                "address": "Paris",
                "action": "reparer",
                "sous_categorie": "smartphone_tablette_et_console",
            },
        )
        payload = _result_payload(body)
        assert payload["location"]["city"] == "Paris"
        assert len(payload["actors"]) == 1
        assert len(payload["attempts"]) == 1

    def test_widens_radius_on_empty(self, client, monkeypatch):
        actor = {
            "nom": "Y",
            "adresse": "1",
            "code_postal": "75001",
            "ville": "Paris",
            "latitude": 48.86,
            "longitude": 2.35,
            "paternite": "ADEME",
        }
        # First two ADEME calls return empty, third returns one actor.
        monkeypatch.setattr(
            api_client.requests,
            "get",
            self._make_get([self._ban_feature()], [[], [], [actor]]),
        )
        body = _call(
            client,
            "find_circular_solution",
            {
                "address": "Paris",
                "action": "reparer",
                "sous_categorie": "velo",
                "radius_meters": 5000,
            },
        )
        payload = _result_payload(body)
        assert len(payload["actors"]) == 1
        # Three attempts: 5000, 10000, 20000
        assert [a["radius_meters"] for a in payload["attempts"]] == [5000, 10000, 20000]

    def test_empty_after_all_widening(self, client, monkeypatch):
        # Every ADEME call returns empty — radius walks 5000→10k→20k→40k→50k
        monkeypatch.setattr(
            api_client.requests,
            "get",
            self._make_get(
                [self._ban_feature()],
                [[], [], [], [], []],
            ),
        )
        body = _call(
            client,
            "find_circular_solution",
            {
                "address": "Paris",
                "action": "reparer",
                "sous_categorie": "velo",
            },
        )
        payload = _result_payload(body)
        assert payload["actors"] == []
        assert "quefairedemesdechets.ademe.fr" in payload["message"]

    def test_unknown_address_returns_message(self, client, monkeypatch):
        monkeypatch.setattr(
            api_client.requests,
            "get",
            lambda *a, **kw: _fake_response({"features": []}),
        )
        body = _call(
            client,
            "find_circular_solution",
            {
                "address": "kjsdflkjsdf",
                "action": "reparer",
                "sous_categorie": "velo",
            },
        )
        payload = _result_payload(body)
        assert payload["location"] is None
        assert payload["actors"] == []


@pytest.mark.django_db
class TestErrorHandling:
    def test_invalid_json_returns_parse_error(self, client):
        response = client.post(
            MCP_URL, data="{not json", content_type="application/json"
        )
        assert response.status_code == 400
        assert response.json()["error"]["code"] == -32700

    def test_unknown_method_returns_method_not_found(self, client):
        body = _rpc(client, "totally/unknown").json()
        assert body["error"]["code"] == -32601

    def test_get_is_rejected(self, client):
        response = client.get(MCP_URL)
        assert response.status_code == 405


@pytest.mark.django_db
class TestBatch:
    def test_batch_request_returns_array(self, client):
        batch = [
            {"jsonrpc": "2.0", "id": 1, "method": "ping"},
            {"jsonrpc": "2.0", "id": 2, "method": "tools/list"},
        ]
        response = client.post(
            MCP_URL, data=json.dumps(batch), content_type="application/json"
        )
        assert response.status_code == 200
        body = response.json()
        assert isinstance(body, list)
        assert len(body) == 2
        assert {r["id"] for r in body} == {1, 2}
