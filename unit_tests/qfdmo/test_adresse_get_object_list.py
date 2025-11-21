import json

import pytest
from django.urls import reverse

from qfdmd.models import Synonyme
from unit_tests.qfdmd.qfdmod_factory import ProduitFactory, SynonymeFactory
from unit_tests.qfdmo.sscatobj_factory import SousCategorieObjetFactory


@pytest.fixture
def sous_categorie_reemploi_possible():
    return SousCategorieObjetFactory()


@pytest.fixture
def sous_categorie_not_reemploi_possible():
    return SousCategorieObjetFactory(reemploi_possible=False)


@pytest.fixture
def produit_reemploi_possible(sous_categorie_reemploi_possible):
    produit = ProduitFactory()
    produit.sous_categories.add(sous_categorie_reemploi_possible)
    return produit


@pytest.fixture
def produit_not_reemploi_possible(sous_categorie_not_reemploi_possible):
    produit = ProduitFactory()
    produit.sous_categories.add(sous_categorie_not_reemploi_possible)
    return produit


@pytest.fixture
def synonymes_reemploi_possible(produit_reemploi_possible) -> list[Synonyme]:
    synonymes = []
    for i in range(20):
        synonymes.append(
            SynonymeFactory(
                nom=f"Test Synonyme Reemploi Possible {i}",
                produit=produit_reemploi_possible,
            )
        )
    return synonymes


@pytest.fixture
def synonymes_not_reemploi_possible(produit_not_reemploi_possible) -> list[Synonyme]:
    synonymes = []
    Synonyme.objects.all().delete()
    for i in range(20):
        synonymes.append(
            SynonymeFactory(
                nom=f"Test Synonyme Not Reemploi Possible {i}",
                produit=produit_not_reemploi_possible,
            )
        )
    return synonymes


@pytest.mark.django_db
def test_get_synonyme_list_noquery(client):
    url = reverse("qfdmo:get_synonyme_list")
    response = client.get(url)
    assert response.status_code == 200
    data = json.loads(response.content)
    assert data == []


@pytest.mark.django_db
def test_get_synonyme_list(client, synonymes_reemploi_possible):
    url = reverse("qfdmo:get_synonyme_list")
    response = client.get(url, {"q": "Test Synonyme"})

    assert response.status_code == 200
    data = json.loads(response.content)
    assert len(data) == 10
    assert all(obj["label"].startswith("Test Synonyme") for obj in data)


@pytest.mark.django_db
def test_get_synonyme_list_most_accurate_first(
    client, synonymes_reemploi_possible, synonymes_not_reemploi_possible
):
    url = reverse("qfdmo:get_synonyme_list")
    response = client.get(url, {"q": "Test Synonyme Not Reemploi Possible"})

    assert response.status_code == 200
    data = json.loads(response.content)
    assert len(data) == 10
    assert all(
        obj["label"].startswith("Test Synonyme Not Reemploi Possible") for obj in data
    )


@pytest.mark.django_db
def test_get_synonyme_list_only_reemploi_no_result(
    client, synonymes_not_reemploi_possible
):
    url = reverse("qfdmo:get_synonyme_list")
    response = client.get(
        url, {"q": "Test Synonyme Not Reemploi Possible", "only_reemploi": True}
    )
    assert response.status_code == 200
    data = json.loads(response.content)
    assert len(data) == 0


@pytest.mark.django_db
def test_get_synonyme_list_only_reemploi(
    client, synonymes_not_reemploi_possible, synonymes_reemploi_possible
):
    url = reverse("qfdmo:get_synonyme_list")
    response = client.get(
        url, {"q": "Test Synonyme Not Reemploi Possible", "only_reemploi": True}
    )
    assert response.status_code == 200
    data = json.loads(response.content)
    assert len(data) == 10
    assert all(
        obj["label"].startswith("Test Synonyme Reemploi Possible") for obj in data
    )
