from unittest.mock import patch

import pytest
from django.contrib.auth.models import User
from django.core.management import call_command
from django.test import Client

from qfdmd.models import Produit, Synonyme
from search.score_breakdown import compute_breakdown


@pytest.fixture
def produit():
    return Produit.objects.create(nom="Mouchoir score test")


@pytest.fixture
def synonyme_with_variant(produit):
    syn = Synonyme.objects.create(
        nom="Mouchoir score test",
        produit=produit,
        search_variants="kleenex score",
    )
    call_command("rebuild_modelsearch_index")
    return syn


@pytest.fixture
def beta_user(db):
    return User.objects.create_user(username="beta-tester", password="x")


@pytest.fixture
def beta_client(beta_user):
    client = Client()
    client.force_login(beta_user)
    return client


@pytest.mark.django_db
class TestComputeBreakdown:
    def test_returns_empty_for_blank_query(self):
        assert compute_breakdown("", [1, 2, 3]) == {}

    def test_returns_empty_for_no_pks(self):
        assert compute_breakdown("kleenex", []) == {}

    def test_breakdown_for_matching_synonyme(self, synonyme_with_variant):
        breakdown = compute_breakdown(
            "mouchoir", [synonyme_with_variant.searchterm_ptr_id]
        )

        result = breakdown[synonyme_with_variant.searchterm_ptr_id]
        assert result.title_sim > 0.0
        assert 0.0 <= result.body_sim <= 1.0
        assert result.title_norm > 0.0
        assert result.ranked > 0.0

    def test_variant_match_lights_up_body_sim(self, synonyme_with_variant):
        breakdown = compute_breakdown(
            "kleenex", [synonyme_with_variant.searchterm_ptr_id]
        )

        result = breakdown[synonyme_with_variant.searchterm_ptr_id]
        # Variant matches show up on body_text, not title_text.
        assert result.body_sim > result.title_sim


@pytest.mark.django_db
class TestAutocompleteScoreBreakdownContext:
    """The view exposes score_breakdown in context only for beta users."""

    @patch("qfdmd.middleware.has_explicit_perm")
    def test_no_breakdown_for_non_beta(
        self, mock_has_perm, beta_client, synonyme_with_variant
    ):
        mock_has_perm.return_value = False

        response = beta_client.get("/assistant/autocomplete-search", {"q": "mouchoir"})

        assert response.status_code == 200
        assert "score_breakdown" not in response.context
        assert b"score-breakdown-" not in response.content

    @patch("qfdmd.middleware.has_explicit_perm")
    def test_breakdown_rendered_for_beta(
        self, mock_has_perm, beta_client, synonyme_with_variant
    ):
        mock_has_perm.return_value = True

        response = beta_client.get("/assistant/autocomplete-search", {"q": "mouchoir"})

        assert response.status_code == 200
        assert "score_breakdown" in response.context
        assert response.context["score_breakdown"]
        assert b"score-breakdown-" in response.content
        assert "Title&nbsp;sim.".encode() in response.content
