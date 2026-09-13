from unittest.mock import patch

import pytest
from django.core.cache import cache
from django.test import override_settings
from django.urls import reverse

# Les réglages de test utilisent DummyCache, qui ne mémorise rien : les deux
# tests portant sur le cache ont besoin d'un vrai backend pour dire quoi que ce
# soit.
CACHE_EN_MEMOIRE = override_settings(
    CACHES={
        "default": {
            "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
            "LOCATION": "test-adresse",
        }
    }
)

pytestmark = pytest.mark.django_db


def reponse_ban(*elements):
    """Imite la réponse de la BAN, dont seule la forme nous intéresse ici."""

    class Fausse:
        @staticmethod
        def raise_for_status():
            return None

        @staticmethod
        def json():
            return {"features": list(elements)}

    return Fausse()


def element(label, type_ban, longitude=2.35, latitude=48.85, context="75, Paris"):
    return {
        "properties": {"label": label, "type": type_ban, "context": context},
        "geometry": {"coordinates": [longitude, latitude]},
    }


@pytest.fixture(autouse=True)
def cache_vide():
    cache.clear()
    yield
    cache.clear()


class TestRechercheAdresse:
    def test_saisie_trop_courte_ne_touche_pas_la_ban(self, client):
        with patch("assistant.views.adresse.requests.get") as requete:
            reponse = client.get(reverse("assistant:recherche-adresse"), {"q": "ab"})

        assert reponse.json() == {"resultats": []}
        requete.assert_not_called()

    def test_adresse_precise(self, client):
        with patch(
            "assistant.views.adresse.requests.get",
            return_value=reponse_ban(
                element("8 Rue de Rivoli 75004 Paris", "housenumber")
            ),
        ):
            resultats = client.get(
                reverse("assistant:recherche-adresse"), {"q": "8 rue de rivoli"}
            ).json()["resultats"]

        assert resultats == [
            {
                "libelle": "8 Rue de Rivoli 75004 Paris",
                "detail": "75, Paris",
                "longitude": 2.35,
                "latitude": 48.85,
                "precise": True,
            }
        ]

    @pytest.mark.parametrize(
        "type_ban,precise",
        [
            ("housenumber", True),
            ("street", True),
            ("locality", True),
            ("municipality", False),
        ],
    )
    def test_seule_une_commune_n_est_pas_precise(self, client, type_ban, precise):
        """La punaise rouge ne s'affiche que pour un point précis (#3356)."""
        with patch(
            "assistant.views.adresse.requests.get",
            return_value=reponse_ban(element("Lyon", type_ban)),
        ):
            resultats = client.get(
                reverse("assistant:recherche-adresse"), {"q": "lyon"}
            ).json()["resultats"]

        assert resultats[0]["precise"] is precise

    def test_panne_ban_rend_une_liste_vide(self, client):
        import requests

        with patch(
            "assistant.views.adresse.requests.get",
            side_effect=requests.RequestException("injoignable"),
        ):
            reponse = client.get(reverse("assistant:recherche-adresse"), {"q": "paris"})

        assert reponse.status_code == 200
        assert reponse.json() == {"resultats": []}

    @CACHE_EN_MEMOIRE
    def test_une_panne_n_est_pas_mise_en_cache(self, client):
        """Sinon une indisponibilité passagère se figerait pour 24 h."""
        import requests

        with patch(
            "assistant.views.adresse.requests.get",
            side_effect=requests.RequestException("injoignable"),
        ):
            client.get(reverse("assistant:recherche-adresse"), {"q": "paris"})

        with patch(
            "assistant.views.adresse.requests.get",
            return_value=reponse_ban(element("Paris", "municipality")),
        ) as requete:
            resultats = client.get(
                reverse("assistant:recherche-adresse"), {"q": "paris"}
            ).json()["resultats"]

        requete.assert_called_once()
        assert resultats[0]["libelle"] == "Paris"

    @CACHE_EN_MEMOIRE
    def test_le_cache_evite_un_second_appel(self, client):
        with patch(
            "assistant.views.adresse.requests.get",
            return_value=reponse_ban(element("Auray", "municipality")),
        ) as requete:
            client.get(reverse("assistant:recherche-adresse"), {"q": "auray"})
            client.get(reverse("assistant:recherche-adresse"), {"q": "AURAY"})

        requete.assert_called_once()

    def test_element_inexploitable_est_ignore(self, client):
        """La BAN peut renvoyer un élément sans libellé ou sans coordonnées."""
        with patch(
            "assistant.views.adresse.requests.get",
            return_value=reponse_ban(
                {"properties": {"type": "street"}, "geometry": {}},
                element("Auray", "municipality"),
            ),
        ):
            resultats = client.get(
                reverse("assistant:recherche-adresse"), {"q": "auray"}
            ).json()["resultats"]

        assert [r["libelle"] for r in resultats] == ["Auray"]
