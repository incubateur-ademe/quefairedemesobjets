from urllib.parse import urlencode

import pytest
from django.contrib.gis.geos import Point
from django.core.management import call_command

from qfdmo.models.acteur import ActeurService, ActeurStatus, DisplayedActeur, Source
from qfdmo.models.action import Action, GroupeAction
from qfdmo.models.categorie_objet import SousCategorieObjet
from unit_tests.qfdmo.acteur_factory import (
    DisplayedActeurFactory,
    DisplayedPropositionServiceFactory,
    SourceFactory,
)
from unit_tests.qfdmo.sscatobj_factory import SousCategorieObjetFactory

BASE_URL = "http://localhost:8000/api/qfdmo"


# Fixtures
# --------
@pytest.fixture
def sous_categorie():
    sous_categorie = SousCategorieObjetFactory()
    return sous_categorie


@pytest.fixture
def displayed_acteur():
    DisplayedActeurFactory(
        pk="UN-ACTEUR", location=Point(2.3, 48.86), statut=ActeurStatus.ACTIF
    )


@pytest.fixture(scope="session")
def django_db_setup(django_db_setup, django_db_blocker):
    with django_db_blocker.unblock():
        call_command(
            "loaddata_with_computed_fields",
            "produits",
            "categories",
            "actions",
            "acteur_services",
            "acteur_types",
        )


# Tests
# -----
@pytest.mark.django_db
def test_get_actions(client):
    """Test the /actions endpoint"""
    response = client.get(f"{BASE_URL}/actions")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == Action.objects.count()
    if data:
        assert "code" in data[0]
        assert "id" in data[0]
        assert "libelle" in data[0]


@pytest.mark.django_db
def test_get_groupe_actions(client):
    """Test the /actions/groupes endpoint"""
    response = client.get(f"{BASE_URL}/actions/groupes")
    assert response.status_code == 200
    assert isinstance(response.json(), list)
    assert len(response.json()) == GroupeAction.objects.filter(afficher=True).count()


@pytest.mark.django_db
def test_get_acteurs(client, displayed_acteur):
    """Test the /acteurs endpoint with filters"""
    params = {
        "latitude": 48.86,
        "longitude": 2.3,
        "rayon": 5,
    }
    response = client.get(f"{BASE_URL}/acteurs?{urlencode(params)}")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data["items"], list)
    assert data["count"] > 0

    returned_acteur = data["items"][0]
    assert "nom" in returned_acteur
    assert "adresse" in returned_acteur
    assert returned_acteur["identifiant_unique"] == "UN-ACTEUR"


@pytest.mark.django_db
def test_get_acteurs_sous_categorie_filter(client, displayed_acteur):
    """Test the /acteurs endpoint with sous categorie filter"""
    acteur = DisplayedActeurFactory(
        pk="UN-AUTRE-ACTEUR", location=Point(2.3, 48.86), statut=ActeurStatus.ACTIF
    )
    sous_categorie = SousCategorieObjetFactory(id=666)
    proposition_service = DisplayedPropositionServiceFactory(acteur=acteur)
    proposition_service.sous_categories.add(sous_categorie)

    params = {"latitude": 48.86, "longitude": 2.3, "rayon": 5, "sous_categories": 666}
    response = client.get(f"{BASE_URL}/acteurs?{urlencode(params)}")
    data = response.json()

    assert SousCategorieObjet.objects.filter(id=666).exists()
    assert DisplayedActeur.objects.filter(statut=ActeurStatus.ACTIF).count() == 2
    assert (
        DisplayedActeur.objects.filter(
            statut=ActeurStatus.ACTIF,
            proposition_services__sous_categories__id__in=[666],
        ).count()
        == 1
    )
    assert data["count"] == 1


@pytest.mark.django_db
def test_get_acteurs_types(client):
    """Test the /acteurs/types endpoint"""
    response = client.get(f"{BASE_URL}/acteurs/types")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0
    assert "code" in data[0]
    assert "id" in data[0]
    assert "libelle" in data[0]


@pytest.mark.django_db
def test_get_acteurs_services(client):
    """Test the /acteurs/services endpoint"""
    response = client.get(f"{BASE_URL}/acteurs/services")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == ActeurService.objects.all().count()
    assert "code" in data[0]
    assert "id" in data[0]
    assert "libelle" in data[0]


@pytest.mark.django_db
def test_get_acteur_by_identifiant(client):
    """Test the /acteur endpoint"""
    identifiant_unique = "ACT12345"
    DisplayedActeurFactory(pk=identifiant_unique, statut=ActeurStatus.ACTIF)
    response = client.get(
        f"{BASE_URL}/acteur", query_params={"identifiant_unique": identifiant_unique}
    )
    assert response.status_code == 200
    data = response.json()
    assert "nom" in data
    assert "nom_commercial" in data
    assert "siret" in data
    assert "adresse" in data
    assert data.get("identifiant_unique") == identifiant_unique


@pytest.mark.django_db
def test_get_acteur_inacteur_returns_404(client):
    identifiant_unique = "INACTIF_ACT12345"
    DisplayedActeurFactory(pk=identifiant_unique, statut=ActeurStatus.INACTIF)
    response = client.get(
        f"{BASE_URL}/acteur", query_params={"identifiant_unique": identifiant_unique}
    )
    assert response.status_code == 404


@pytest.mark.django_db
def test_autocomplete_epci(client, mocker):
    """Test the /autocomplete/configurateur endpoint"""
    # Mock setup
    mock_formatted_epcis_list = mocker.patch("qfdmo.geo_api.formatted_epcis_list")
    mock_formatted_epcis_list.return_value = [
        "200043123 - CC Auray Quiberon Terre Atlantique",
        "200043156 - CC du Pays Rethélois",
    ]

    # Simulate a successful response
    response = client.get(
        f"{BASE_URL}/autocomplete/configurateur", query_params={"query": "Quiberon"}
    )

    # Assertions
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 2
    if data:
        assert "Quiberon" in data[0]


@pytest.mark.django_db
def test_get_sources(client):
    """Test the /sources endpoint"""
    displayed_source = SourceFactory(afficher=True)
    hidden_source = SourceFactory(afficher=False)

    response = client.get(f"{BASE_URL}/sources")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == Source.objects.filter(afficher=True).count()
    data_ids = {source["id"] for source in data}
    assert displayed_source.id in data_ids
    assert hidden_source.id not in data_ids
    if data:
        assert "code" in data[0]
        assert "id" in data[0]
        assert "libelle" in data[0]
        assert "url" in data[0]


@pytest.mark.django_db
def test_get_sous_categories(client):
    """Test the /sous-categories endpoint"""
    displayed_sous_categorie = SousCategorieObjetFactory(afficher=True)
    hidden_sous_categorie = SousCategorieObjetFactory(afficher=False)

    response = client.get(f"{BASE_URL}/sous-categories")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == SousCategorieObjet.objects.filter(afficher=True).count()
    data_ids = {sous_categorie["id"] for sous_categorie in data}
    assert displayed_sous_categorie.id in data_ids
    assert hidden_sous_categorie.id not in data_ids
    if data:
        assert "code" in data[0]
        assert "id" in data[0]
        assert "libelle" in data[0]
