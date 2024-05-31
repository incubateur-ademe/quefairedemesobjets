import json

import pytest
from django.urls import reverse

from unit_tests.qfdmo.sscatobj_factory import ObjetFactory, SousCategorieObjetFactory


@pytest.fixture
def sous_categorie():
    return SousCategorieObjetFactory()


@pytest.fixture
def objet1(sous_categorie):
    return ObjetFactory(libelle="Test Object 1", sous_categorie=sous_categorie)


@pytest.fixture
def objet2(sous_categorie):
    return ObjetFactory(libelle="Test Object 2", sous_categorie=sous_categorie)


@pytest.mark.django_db
def test_get_object_list(client, objet1, objet2):
    url = reverse("qfdmo:get_object_list")
    response = client.get(url, {"q": "Test Object"})

    assert response.status_code == 200
    data = json.loads(response.content)
    assert len(data) == 2
    for obj in data:
        assert obj["label"] in ["Test Object 1", "Test Object 2"]


@pytest.mark.django_db
def test_get_object_list_most_accurate_first(client, objet1, objet2):
    url = reverse("qfdmo:get_object_list")
    response = client.get(url, {"q": "Test Object 2"})

    assert response.status_code == 200
    data = json.loads(response.content)
    assert len(data) == 2
    assert data[0]["label"] == "Test Object 2"


@pytest.mark.django_db
def test_get_object_list_sscat_not_displayed(client, sous_categorie, objet1, objet2):
    sous_categorie.afficher = False
    sous_categorie.save()
    url = reverse("qfdmo:get_object_list")
    response = client.get(url, {"q": "Test Object 2"})
    assert response.status_code == 200
    data = json.loads(response.content)
    assert len(data) == 0


@pytest.mark.django_db
def test_get_object_list_limit_to_ten(client):
    for i in range(11):
        ObjetFactory(libelle=f"Test Object {i}")
    url = reverse("qfdmo:get_object_list")
    response = client.get(url, {"q": "Test Object"})

    assert response.status_code == 200
    data = json.loads(response.content)
    assert len(data) == 10
