import pytest
from django.urls import reverse

from assistant.parcours import Parcours

pytestmark = pytest.mark.django_db


class TestParcours:
    def test_lit_une_saisie_complete(self):
        parcours = Parcours.depuis(
            {
                "objet": "chaise",
                "adresse": "8 Rue de Rivoli 75004 Paris",
                "longitude": "2.35",
                "latitude": "48.85",
                "precise": "true",
            }
        )

        assert parcours.localise
        assert parcours.precise
        assert parcours.longitude == 2.35

    def test_une_coordonnee_illisible_vaut_absence(self):
        """L'usager a tapé une adresse sans choisir de suggestion."""
        parcours = Parcours.depuis({"adresse": "Paris", "longitude": "abc"})

        assert not parcours.localise
        assert parcours.adresse == "Paris"

    def test_une_commune_n_est_pas_precise(self):
        parcours = Parcours.depuis({"adresse": "Lyon", "precise": ""})

        assert not parcours.precise

    def test_les_valeurs_vides_ne_sont_pas_transportees(self):
        parcours = Parcours.depuis({"objet": "chaise"})

        assert parcours.en_parametres() == {"objet": "chaise"}

    def test_aller_retour_par_les_parametres(self):
        depart = Parcours(
            objet="chaise",
            adresse="Auray",
            longitude=-2.98,
            latitude=47.66,
            precise=False,
        )

        arrivee = Parcours.depuis(depart.en_parametres())

        assert arrivee == depart


class TestRechercheView:
    def test_saisie_complete_mene_a_la_fiche(self, client):
        reponse = client.get(
            reverse("assistant:recherche"),
            {"slug": "emballages", "objet": "Emballages", "adresse": "Auray"},
        )

        assert reponse.status_code == 302
        assert reponse.url.startswith(
            reverse("assistant:produit", kwargs={"slug": "emballages"})
        )

    def test_le_parcours_suit_jusqu_a_la_fiche(self, client):
        reponse = client.get(
            reverse("assistant:recherche"),
            {
                "slug": "emballages",
                "objet": "Emballages",
                "adresse": "Auray",
                "longitude": "-2.98",
                "latitude": "47.66",
            },
        )

        assert "longitude=-2.98" in reponse.url
        assert "adresse=Auray" in reponse.url

    @pytest.mark.parametrize(
        "parametres",
        [
            {"objet": "Emballages", "adresse": "Auray"},  # pas de slug : rien choisi
            {"slug": "emballages", "objet": "Emballages"},  # pas d'adresse
        ],
    )
    def test_saisie_incomplete_revient_a_l_accueil(self, client, parametres):
        """Les deux champs sont obligatoires (#3295)."""
        reponse = client.get(reverse("assistant:recherche"), parametres)

        assert reponse.status_code == 302
        assert reponse.url.startswith(reverse("assistant:home"))

    def test_la_saisie_deja_faite_n_est_pas_perdue(self, client):
        reponse = client.get(
            reverse("assistant:recherche"), {"objet": "Emballages", "adresse": ""}
        )

        assert "objet=Emballages" in reponse.url


class TestAccueil:
    def test_les_deux_champs_sont_obligatoires(self, client):
        contenu = client.get(reverse("assistant:home")).content.decode()

        assert contenu.count("required") >= 2

    def test_les_champs_caches_de_l_adresse_sont_presents(self, client):
        """Sans eux, la carte n'a pas de position à afficher."""
        contenu = client.get(reverse("assistant:home")).content.decode()

        for nom in ("longitude", "latitude", "precise"):
            assert f'name="{nom}"' in contenu
