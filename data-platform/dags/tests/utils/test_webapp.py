from unittest.mock import MagicMock, patch

import pytest
import requests
from utils.webapp import (
    get_acteur_columns_from_webapp,
    get_acteur_types_from_webapp,
    get_sources_from_webapp,
)

SOURCES = [{"id": 1, "code": "source1", "libelle": "Source 1"}]
ACTEUR_TYPES = [{"id": 10, "code": "type1", "libelle": "Type 1"}]
ACTEUR_COLUMNS = {
    "vue_acteur": {"with_properties": ["nom", "latitude"], "db_only": ["nom"]},
    "revision_acteur": {"with_properties": ["nom"], "db_only": ["nom"]},
}


@pytest.fixture(autouse=True)
def clear_cache():
    get_sources_from_webapp.cache_clear()
    get_acteur_types_from_webapp.cache_clear()
    get_acteur_columns_from_webapp.cache_clear()
    yield
    get_sources_from_webapp.cache_clear()
    get_acteur_types_from_webapp.cache_clear()
    get_acteur_columns_from_webapp.cache_clear()


class TestGetSourcesFromWebapp:

    def test_calls_webapp_api(self, monkeypatch):
        monkeypatch.setattr("utils.webapp.WEBAPP_URL", "https://webapp.example.org")
        response = MagicMock()
        response.json.return_value = SOURCES
        with patch("utils.webapp.requests.get", return_value=response) as mock_get:
            assert get_sources_from_webapp() == SOURCES
        args, kwargs = mock_get.call_args
        assert args[0] == "https://webapp.example.org/api/qfdmo/sources"
        assert kwargs["timeout"]

    def test_result_is_cached(self, monkeypatch):
        monkeypatch.setattr("utils.webapp.WEBAPP_URL", "https://webapp.example.org")
        response = MagicMock()
        response.json.return_value = SOURCES
        with patch("utils.webapp.requests.get", return_value=response) as mock_get:
            get_sources_from_webapp()
            get_sources_from_webapp()
        assert mock_get.call_count == 1

    def test_explicit_error_when_unreachable(self):
        with patch("utils.webapp.requests.get", side_effect=requests.ConnectionError()):
            with pytest.raises(RuntimeError, match="Webapp API unreachable"):
                get_sources_from_webapp()


class TestGetActeurTypesFromWebapp:
    def test_calls_webapp_api(self, monkeypatch):
        monkeypatch.setattr("utils.webapp.WEBAPP_URL", "https://webapp.example.org")
        response = MagicMock()
        response.json.return_value = ACTEUR_TYPES
        with patch("utils.webapp.requests.get", return_value=response) as mock_get:
            assert get_acteur_types_from_webapp() == ACTEUR_TYPES
        args, kwargs = mock_get.call_args
        assert args[0] == "https://webapp.example.org/api/qfdmo/acteurs/types"
        assert kwargs["timeout"]


class TestGetActeurColumnsFromWebapp:

    def test_calls_webapp_api(self, monkeypatch):
        monkeypatch.setattr("utils.webapp.WEBAPP_URL", "https://webapp.example.org")
        response = MagicMock()
        response.json.return_value = ACTEUR_COLUMNS
        with patch("utils.webapp.requests.get", return_value=response) as mock_get:
            assert get_acteur_columns_from_webapp() == ACTEUR_COLUMNS
        args, kwargs = mock_get.call_args
        assert args[0] == "https://webapp.example.org/api/qfdmo/acteurs/columns"
        assert kwargs["timeout"]
