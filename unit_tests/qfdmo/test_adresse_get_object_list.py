import json

import pytest
from django.urls import reverse

from qfdmd.models import Synonyme
from unit_tests.qfdmd.qfdmod_factory import ProduitFactory, SynonymeFactory
from unit_tests.qfdmo.sscatobj_factory import SousCategorieObjetFactory


@pytest.fixture
def sous_categorie():
    return SousCategorieObjetFactory()


@pytest.fixture
def produit(sous_categorie):
    produit = ProduitFactory()
    produit.sous_categories.add(sous_categorie)
    return produit


@pytest.fixture
def synonymes(produit) -> list[Synonyme]:
    synonyme1 = SynonymeFactory(nom="Test Object 1", produit=produit)
    synonyme2 = SynonymeFactory(nom="Test Object 2", produit=produit)
    return [synonyme1, synonyme2]


def test_get_object_list_noquery(client):
    url = reverse("qfdmo:get_object_list")
    response = client.get(url)
    assert response.status_code == 200
    data = json.loads(response.content)
    assert data == []


@pytest.mark.django_db
def test_get_object_list(client, synonymes):
    url = reverse("qfdmo:get_object_list")
    response = client.get(url, {"q": "Test Object"})

    assert response.status_code == 200
    data = json.loads(response.content)
    assert len(data) == 2
    for obj in data:
        assert obj["label"] in ["Test Object 1", "Test Object 2"]


@pytest.mark.django_db
def test_get_object_list_most_accurate_first(client, synonymes):
    url = reverse("qfdmo:get_object_list")
    response = client.get(url, {"q": "Test Object 2"})

    assert response.status_code == 200
    data = json.loads(response.content)
    assert len(data) == 2
    assert data[0]["label"] == "Test Object 2"
    assert data[1]["label"] == "Test Object 1"


@pytest.mark.django_db
def test_get_object_list_sscat_not_displayed(client, sous_categorie, synonymes):
    sous_categorie.reemploi_possible = False
    sous_categorie.save()
    url = reverse("qfdmo:get_object_list")
    response = client.get(url, {"q": "Test Object 2"})
    assert response.status_code == 200
    data = json.loads(response.content)
    assert len(data) == 0


@pytest.mark.django_db
def test_get_object_list_limit_to_ten(client, produit):
    for i in range(11):
        SynonymeFactory(nom=f"Test Object {i}", produit=produit)
    url = reverse("qfdmo:get_object_list")
    response = client.get(url, {"q": "Test Object"})

    assert response.status_code == 200
    data = json.loads(response.content)
    assert len(data) == 10
