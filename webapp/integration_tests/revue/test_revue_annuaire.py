from unittest import mock

import pytest
import requests
from data.models.suggestion import SuggestionAction, SuggestionUnitaire
from data.revue.annuaire import identifiants
from django.contrib.auth.models import User
from unit_tests.data.models.suggestion_factory import (
    SuggestionCohorteFactory,
    SuggestionGroupeFactory,
)
from unit_tests.qfdmo.acteur_factory import ActeurFactory, RevisionActeurFactory

API = "/api/suggestions/annuaire-entreprises"

ENTREPRISE = {
    "siren": "130025265",
    "nom_complet": "DINUM",
    "activite_principale": "84.11Z",
    "etat_administratif": "A",
    "siege": {
        "siret": "13002526500013",
        "adresse": "20 AVENUE DE SEGUR 75007 PARIS",
        "activite_principale": "84.11Z",
        "etat_administratif": "A",
        "est_siege": True,
    },
    "matching_etablissements": [
        {
            "siret": "13002526500021",
            "adresse": "1 RUE DE LA PAIX 69001 LYON",
            "activite_principale": "62.01Z",
            "etat_administratif": "F",
            "liste_enseignes": ["ANTENNE LYON"],
            "est_siege": False,
            "latitude": "45.76",
            "longitude": "4.83",
        }
    ],
}


@pytest.fixture
def client(client):
    client.force_login(User.objects.create_user(username="admin", is_superuser=True))
    return client


def api_answer(*results):
    response = mock.Mock()
    response.json.return_value = {"results": list(results)}
    response.raise_for_status.return_value = None
    return response


@pytest.mark.django_db
class TestLookup:
    @mock.patch("data.revue.annuaire.requests.get")
    def test_siret_gives_entreprise_and_etablissement(self, get, client):
        get.return_value = api_answer(ENTREPRISE)

        response = client.get(API, {"champ": "siret", "valeur": "130 025 265 00021"})

        assert response.status_code == 200
        assert response.json() == {
            "trouve": True,
            "entreprise": {
                "siren": "130025265",
                "nom": "DINUM",
                "adresse": "20 AVENUE DE SEGUR 75007 PARIS",
                "activite_code": "84.11Z",
                "etat": "actif",
            },
            "etablissement": {
                "siret": "13002526500021",
                "nom": "ANTENNE LYON",
                "adresse": "1 RUE DE LA PAIX 69001 LYON",
                "activite_code": "62.01Z",
                "etat": "ferme",
                "est_siege": False,
                "latitude": 45.76,
                "longitude": 4.83,
            },
        }
        assert get.call_args.kwargs["params"]["q"] == "13002526500021"

    @mock.patch("data.revue.annuaire.requests.get")
    def test_siren_of_a_ceased_entreprise(self, get, client):
        get.return_value = api_answer({**ENTREPRISE, "etat_administratif": "C"})

        body = client.get(API, {"champ": "siren", "valeur": "130025265"}).json()

        assert body["entreprise"]["etat"] == "inactif"
        assert body["etablissement"] is None

    @mock.patch("data.revue.annuaire.requests.get")
    def test_not_found(self, get, client):
        get.return_value = api_answer({**ENTREPRISE, "siren": "999999999"})

        body = client.get(API, {"champ": "siren", "valeur": "130025265"}).json()

        assert body == {"trouve": False, "entreprise": None, "etablissement": None}

    @mock.patch("data.revue.annuaire.requests.get")
    def test_api_unavailable(self, get, client):
        get.side_effect = requests.Timeout()

        response = client.get(API, {"champ": "siren", "valeur": "130025265"})

        assert response.status_code == 502
        assert response.json()["code"] == "annuaire_unavailable"

    def test_invalid_value(self, client):
        response = client.get(API, {"champ": "siret", "valeur": "1234"})
        assert response.status_code == 422


@pytest.mark.django_db
class TestIdentifiants:
    def test_sources_in_order_without_duplicates(self):
        acteur = ActeurFactory(siret="11111111100011", siren="111111111")
        revision = RevisionActeurFactory(
            identifiant_unique=acteur.identifiant_unique,
            siret="22222222200022",
            siren="111111111",
        )
        parent = RevisionActeurFactory(siret="", siren="333333333")
        groupe = SuggestionGroupeFactory(
            suggestion_cohorte=SuggestionCohorteFactory(
                type_action=SuggestionAction.SOURCE_MODIFICATION
            ),
            acteur=acteur,
            revision_acteur=revision,
            parent_revision_acteur=parent,
        )
        # The source suggests the SIRET already corrected
        SuggestionUnitaire.objects.create(
            suggestion_groupe=groupe,
            suggestion_modele="Acteur",
            acteur_id=acteur.identifiant_unique,
            champs=["siret"],
            valeurs=["22222222200022"],
        )
        displayed = mock.Mock(siret="22222222200022", siren="333333333")

        result = identifiants(groupe, displayed)

        assert [(c["source"], c["valeur"]) for c in result["siret"]] == [
            ("corrige", "22222222200022"),
        ]
        assert [(c["source"], c["valeur"], c["propose"]) for c in result["siren"]] == [
            ("corrige", "333333333", False),
            ("correction", "111111111", False),
        ]
