import json

import pytest

from mcp_server import docs as docs_module
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
        assert "Indication de localisation" not in text

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
class TestTools:
    def test_list_returns_empty(self, client):
        body = _rpc(client, "tools/list").json()
        assert body["result"]["tools"] == []


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
            {"jsonrpc": "2.0", "id": 2, "method": "resources/list"},
        ]
        response = client.post(
            MCP_URL, data=json.dumps(batch), content_type="application/json"
        )
        assert response.status_code == 200
        body = response.json()
        assert isinstance(body, list)
        assert len(body) == 2
        assert {r["id"] for r in body} == {1, 2}
