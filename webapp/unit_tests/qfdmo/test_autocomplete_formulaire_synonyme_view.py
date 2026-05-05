"""Tests for the formulaire synonyme autocomplete view."""

import pytest
from django.urls import reverse

from qfdmd.models import Synonyme
from unit_tests.qfdmd.qfdmod_factory import ProduitFactory, SynonymeFactory
from unit_tests.qfdmo.sscatobj_factory import SousCategorieObjetFactory


@pytest.fixture
def sous_categorie_reemploi():
    return SousCategorieObjetFactory(libelle="Pantalon")


@pytest.fixture
def sous_categorie_not_reemploi():
    return SousCategorieObjetFactory(
        libelle="Cendre de cheminée",
        reemploi_possible=False,
    )


@pytest.fixture
def produit_reemploi(sous_categorie_reemploi):
    produit = ProduitFactory()
    produit.sous_categories.add(sous_categorie_reemploi)
    return produit


@pytest.fixture
def produit_not_reemploi(sous_categorie_not_reemploi):
    produit = ProduitFactory()
    produit.sous_categories.add(sous_categorie_not_reemploi)
    return produit


@pytest.fixture
def synonymes(produit_reemploi, produit_not_reemploi) -> list[Synonyme]:
    Synonyme.objects.all().delete()
    return [
        SynonymeFactory(nom="Pantalon de jean", produit=produit_reemploi),
        SynonymeFactory(nom="Cendre", produit=produit_not_reemploi),
    ]


@pytest.fixture
def url():
    return reverse("qfdmo:autocomplete_synonyme_formulaire")


pytestmark = pytest.mark.django_db


def test_empty_query_returns_no_options(client, url, synonymes):
    response = client.get(url, {"q": "", "turbo_frame_id": "test"})
    assert response.status_code == 200
    body = response.content.decode()
    assert 'role="listbox"' in body
    assert 'role="option"' not in body


def test_query_returns_options_with_sc_id(client, url, synonymes):
    response = client.get(url, {"q": "Pantalon", "turbo_frame_id": "test"})
    assert response.status_code == 200
    body = response.content.decode()
    assert 'role="option"' in body
    assert "Pantalon de jean" in body
    assert "data-sc-id=" in body
    assert 'data-value="Pantalon de jean"' in body
    assert 'data-selected-value="Pantalon de jean"' in body


def test_only_reemploi_filters_results(client, url, synonymes):
    response = client.get(
        url,
        {"q": "Cendre", "turbo_frame_id": "test", "only_reemploi": "true"},
    )
    body = response.content.decode()
    # Cendre's sous_categorie has reemploi_possible=False, so it must be filtered out
    assert "Cendre" not in body
