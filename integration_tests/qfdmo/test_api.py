import pytest
from django.contrib.gis.geos import Point

from qfdmo.models.acteur import ActeurStatus
from unit_tests.qfdmo.acteur_factory import DisplayedActeurFactory

BASE_URL = "http://localhost:8000/api/qfdmo"


@pytest.mark.django_db
def test_get_actions(client):
    """Test the /actions endpoint"""
    response = client.get(f"{BASE_URL}/actions")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


@pytest.mark.django_db
def test_get_groupe_actions(client):
    """Test the /actions/groupes endpoint"""
    response = client.get(f"{BASE_URL}/actions/groupes")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


@pytest.mark.django_db
def test_get_acteurs(client):
    """Test the /acteurs endpoint with filters"""
    DisplayedActeurFactory(
        pk="UN-ACTEUR", location=Point(2.3, 48.86), statut=ActeurStatus.ACTIF
    )
    params = {
        "latitude": 48.86,
        "longitude": 2.3,
        "rayon": 5,
    }
    response = client.get(f"{BASE_URL}/acteurs", params=params)
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data["items"], list)
    assert data["count"] > 0

    returned_acteur = data["items"][0]
    assert "nom" in returned_acteur
    assert "adresse" in returned_acteur
    assert returned_acteur["identifiant_unique"] == "UN-ACTEUR"


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
def test_autocomplete_epci(client):
    """Test the /autocomplete/configurateur endpoint"""
    response = client.get(
        f"{BASE_URL}/autocomplete/configurateur", query_params={"query": "Quiberon"}
    )
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 5
    if data:
        assert "Quiberon" in data[0]
