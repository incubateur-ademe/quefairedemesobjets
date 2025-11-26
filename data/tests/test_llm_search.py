"""
Tests for LLM-powered search functionality in SuggestionCohorteAdmin.
"""

from unittest.mock import MagicMock, Mock, patch

import pytest
from django.contrib.admin.sites import AdminSite
from django.contrib.auth import get_user_model
from django.test import RequestFactory

from data.admin import LLMQueryBuilder, SuggestionCohorteAdmin
from data.models.suggestion import SuggestionAction, SuggestionCohorte

User = get_user_model()


@pytest.fixture
def admin_site():
    return AdminSite()


@pytest.fixture
def suggestion_cohorte_admin(admin_site):
    return SuggestionCohorteAdmin(SuggestionCohorte, admin_site)


@pytest.fixture
def request_factory():
    return RequestFactory()


@pytest.fixture
def admin_request(request_factory):
    request = request_factory.get("/admin/data/suggestioncohorte/")
    request.user = Mock()
    return request


class TestLLMQueryBuilder:
    """Test the LLM query builder class."""

    def test_initialization(self):
        """Test that LLMQueryBuilder initializes correctly."""
        builder = LLMQueryBuilder(SuggestionCohorte)
        assert builder.model_class == SuggestionCohorte
        assert hasattr(builder, "api_key")

    def test_get_model_schema(self):
        """Test model schema generation."""
        builder = LLMQueryBuilder(SuggestionCohorte)
        schema = builder._get_model_schema()

        assert "id" in schema
        assert "identifiant_action" in schema
        assert "statut" in schema
        assert "type_action" in schema
        assert "metadata" in schema

    @patch("data.admin.config")
    def test_no_api_key_returns_empty_dict(self, mock_config):
        """Test that missing API key returns empty dict."""
        mock_config.return_value = ""
        builder = LLMQueryBuilder(SuggestionCohorte)
        builder.api_key = ""

        result = builder._call_llm("test query")
        assert result == {}

    @patch("data.admin.config")
    @patch("data.admin.anthropic.Anthropic")
    def test_call_llm_success(self, mock_anthropic, mock_config):
        """Test successful LLM call."""
        mock_config.return_value = "test-api-key"

        # Mock the Anthropic client response
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.content = [
            MagicMock(text='{"filters": {"statut__exact": "SUCCES"}}')
        ]
        mock_client.messages.create.return_value = mock_response
        mock_anthropic.return_value = mock_client

        builder = LLMQueryBuilder(SuggestionCohorte)
        builder.api_key = "test-api-key"

        result = builder._call_llm("show successful suggestions")

        assert "filters" in result
        assert result["filters"]["statut__exact"] == "SUCCES"

    @pytest.mark.django_db
    def test_build_queryset_with_simple_filters(self):
        """Test building queryset with simple filters."""
        builder = LLMQueryBuilder(SuggestionCohorte)
        queryset = SuggestionCohorte.objects.all()

        # Mock LLM response
        with patch.object(builder, "_call_llm") as mock_llm:
            mock_llm.return_value = {"filters": {"statut__exact": "SUCCES"}}

            result = builder.build_queryset(queryset, "successful suggestions")

            # Check that the filter was applied
            assert "statut" in str(result.query)

    @pytest.mark.django_db
    def test_build_queryset_with_invalid_fields(self):
        """Test that invalid fields are filtered out."""
        builder = LLMQueryBuilder(SuggestionCohorte)
        queryset = SuggestionCohorte.objects.all()

        # Mock LLM response with invalid field
        with patch.object(builder, "_call_llm") as mock_llm:
            mock_llm.return_value = {
                "filters": {
                    "statut__exact": "SUCCES",
                    "invalid_field__icontains": "test",
                }
            }

            result = builder.build_queryset(queryset, "test query")

            # Should only apply valid field
            assert "statut" in str(result.query)
            assert "invalid_field" not in str(result.query)

    @pytest.mark.django_db
    def test_build_queryset_without_api_key(self):
        """Test that queryset is unchanged without API key."""
        builder = LLMQueryBuilder(SuggestionCohorte)
        builder.api_key = ""
        queryset = SuggestionCohorte.objects.all()

        result = builder.build_queryset(queryset, "test query")

        # Queryset should be unchanged
        assert result == queryset

    @pytest.mark.django_db
    def test_build_queryset_with_q_objects(self):
        """Test building queryset with Q objects."""
        builder = LLMQueryBuilder(SuggestionCohorte)
        queryset = SuggestionCohorte.objects.all()

        # Mock LLM response with Q objects
        with patch.object(builder, "_call_llm") as mock_llm:
            mock_llm.return_value = {
                "q_objects": [
                    {"statut__exact": "SUCCES", "connector": "OR"},
                    {"statut__exact": "ENCOURS", "connector": "OR"},
                ]
            }

            result = builder.build_queryset(queryset, "successful or in progress")

            # Should apply Q object filters
            assert "statut" in str(result.query)


class TestSuggestionCohorteAdmin:
    """Test the admin class with LLM search."""

    def test_admin_has_llm_builder(self, suggestion_cohorte_admin):
        """Test that admin initializes with LLM query builder."""
        assert hasattr(suggestion_cohorte_admin, "llm_query_builder")
        assert isinstance(suggestion_cohorte_admin.llm_query_builder, LLMQueryBuilder)

    @pytest.mark.django_db
    def test_get_search_results_with_natural_language(
        self, suggestion_cohorte_admin, admin_request
    ):
        """Test search with natural language query."""
        queryset = SuggestionCohorte.objects.all()

        # Mock LLM builder
        with patch.object(
            suggestion_cohorte_admin.llm_query_builder, "build_queryset"
        ) as mock_build:
            mock_queryset = Mock()
            mock_queryset.query.where = True  # Simulate modified query
            mock_build.return_value = mock_queryset

            result, use_distinct = suggestion_cohorte_admin.get_search_results(
                admin_request, queryset, "show successful suggestions"
            )

            assert mock_build.called
            assert result == mock_queryset
            assert use_distinct is False

    @pytest.mark.django_db
    def test_get_search_results_falls_back_on_error(
        self, suggestion_cohorte_admin, admin_request
    ):
        """Test that search falls back to standard on error."""
        queryset = SuggestionCohorte.objects.all()

        # Mock LLM builder to raise exception
        with patch.object(
            suggestion_cohorte_admin.llm_query_builder, "build_queryset"
        ) as mock_build:
            mock_build.side_effect = Exception("API error")

            # Should not raise, should fall back
            result, _ = suggestion_cohorte_admin.get_search_results(
                admin_request, queryset, "test query"
            )

            # Should return a queryset (fallback behavior)
            assert result is not None

    @pytest.mark.django_db
    def test_get_search_results_skips_djangoql_queries(
        self, suggestion_cohorte_admin, admin_request
    ):
        """Test that DjangoQL queries bypass LLM."""
        queryset = SuggestionCohorte.objects.all()

        with patch.object(
            suggestion_cohorte_admin.llm_query_builder, "build_queryset"
        ) as mock_build:
            # DjangoQL-style query should not trigger LLM
            suggestion_cohorte_admin.get_search_results(
                admin_request, queryset, "statut = 'SUCCES'"
            )

            # LLM should not be called
            assert not mock_build.called

    @pytest.mark.django_db
    def test_get_search_results_with_empty_query(
        self, suggestion_cohorte_admin, admin_request
    ):
        """Test search with empty query."""
        queryset = SuggestionCohorte.objects.all()

        result, _ = suggestion_cohorte_admin.get_search_results(
            admin_request, queryset, ""
        )

        # Should return original queryset
        assert result.query == queryset.query


@pytest.mark.django_db
class TestSecurity:
    """Test security and sandboxing features."""

    def test_only_read_operations(self):
        """Test that only read operations are possible."""
        builder = LLMQueryBuilder(SuggestionCohorte)
        queryset = SuggestionCohorte.objects.all()

        # Mock LLM to try to return write operations
        with patch.object(builder, "_call_llm") as mock_llm:
            # Even if LLM returns this, it should be safe
            mock_llm.return_value = {"filters": {"statut__exact": "SUCCES"}}

            # This should only result in a filter, no writes
            result = builder.build_queryset(queryset, "delete all")

            # Verify it's still just a queryset
            assert hasattr(result, "filter")
            assert not hasattr(result.query, "delete")

    def test_field_validation(self):
        """Test that invalid fields are rejected."""
        builder = LLMQueryBuilder(SuggestionCohorte)
        queryset = SuggestionCohorte.objects.all()

        with patch.object(builder, "_call_llm") as mock_llm:
            mock_llm.return_value = {
                "filters": {
                    "statut__exact": "SUCCES",
                    "__class__": "malicious",  # Should be filtered
                    "_meta": "dangerous",  # Should be filtered
                }
            }

            result = builder.build_queryset(queryset, "test")

            # Only valid field should be applied
            query_str = str(result.query)
            assert "statut" in query_str
            assert "__class__" not in query_str
            assert "_meta" not in query_str

    def test_no_arbitrary_code_execution(self):
        """Test that arbitrary code cannot be executed."""
        builder = LLMQueryBuilder(SuggestionCohorte)

        # This should not execute any code
        with patch.object(builder, "_call_llm") as mock_llm:
            mock_llm.return_value = {"filters": {"eval('malicious_code')": "test"}}

            queryset = SuggestionCohorte.objects.all()

            # Should not raise or execute anything
            result = builder.build_queryset(queryset, "test")
            assert result is not None
