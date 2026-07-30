from unittest.mock import MagicMock, patch

import pytest
import requests
from utils.webapp import WEBAPP_URL_DEFAULT, acteurs_metadata, webapp_url

METADATA = {
    "sources": {"source1": 1},
    "acteur_types": {"type1": 10},
    "model_fields": {
        "vue_acteur": {"with_properties": ["nom", "latitude"], "db_only": ["nom"]},
        "revision_acteur": {"with_properties": ["nom"], "db_only": ["nom"]},
    },
}


class TestWebappUrl:
    def test_default(self, monkeypatch):
        monkeypatch.delenv("WEBAPP_URL", raising=False)
        assert webapp_url() == WEBAPP_URL_DEFAULT

    def test_from_env_and_strips_trailing_slash(self, monkeypatch):
        monkeypatch.setenv("WEBAPP_URL", "https://webapp.example.org/")
        assert webapp_url() == "https://webapp.example.org"


class TestActeursMetadata:
    @pytest.fixture(autouse=True)
    def clear_cache(self):
        acteurs_metadata.cache_clear()
        yield
        acteurs_metadata.cache_clear()

    def test_calls_webapp_api(self, monkeypatch):
        monkeypatch.setenv("WEBAPP_URL", "https://webapp.example.org")
        response = MagicMock()
        response.json.return_value = METADATA
        with patch("utils.webapp.requests.get", return_value=response) as mock_get:
            assert acteurs_metadata() == METADATA
        args, kwargs = mock_get.call_args
        assert args[0] == "https://webapp.example.org/api/qfdmo/metadata/acteurs"
        assert kwargs["timeout"]

    def test_result_is_cached(self, monkeypatch):
        monkeypatch.setenv("WEBAPP_URL", "https://webapp.example.org")
        response = MagicMock()
        response.json.return_value = METADATA
        with patch("utils.webapp.requests.get", return_value=response) as mock_get:
            acteurs_metadata()
            acteurs_metadata()
        assert mock_get.call_count == 1

    def test_explicit_error_when_unreachable(self):
        with patch("utils.webapp.requests.get", side_effect=requests.ConnectionError()):
            with pytest.raises(RuntimeError, match="Webapp API unreachable"):
                acteurs_metadata()
