import pytest
from django.urls import reverse

from assistant.parcours import Parcours
from qfdmd.models import ProduitPageSearchTerm

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


@pytest.fixture
def fiche():
    """Une fiche publiée : `ModelChoiceField` vérifie qu'elle existe vraiment."""
    from unit_tests.qfdmd.qfdmod_factory import ProduitPageFactory

    return ProduitPageFactory(parent=None)


class TestRechercheView:
    def test_saisie_complete_mene_a_la_fiche(self, client, fiche):
        reponse = client.get(
            reverse("assistant:recherche"),
            {"fiche": fiche.slug, "objet": fiche.title, "adresse": "Auray"},
        )

        assert reponse.status_code == 302
        assert reponse.url.startswith(
            reverse("assistant:produit", kwargs={"slug": fiche.slug})
        )

    def test_le_parcours_suit_jusqu_a_la_fiche(self, client, fiche):
        reponse = client.get(
            reverse("assistant:recherche"),
            {
                "fiche": fiche.slug,
                "objet": fiche.title,
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
            {"objet": "zzz inconnu", "adresse": "Auray"},  # objet non résolu
            {"objet": "Emballages"},  # pas d'adresse
        ],
    )
    def test_saisie_incomplete_reaffiche_l_accueil(self, client, parametres):
        """Les deux champs sont obligatoires (#3295). L'accueil est réaffiché
        avec ses messages plutôt que redirigé : une redirection les perdrait."""
        reponse = client.get(reverse("assistant:recherche"), parametres)

        assert reponse.status_code == 200
        assert "qfa-combobox__erreur" in reponse.content.decode()


class TestAccueil:
    def test_les_deux_champs_sont_obligatoires(self, client):
        contenu = client.get(reverse("assistant:home")).content.decode()

        assert contenu.count("required") >= 2

    def test_les_champs_caches_de_l_adresse_sont_presents(self, client):
        """Sans eux, la carte n'a pas de position à afficher."""
        contenu = client.get(reverse("assistant:home")).content.decode()

        for nom in ("longitude", "latitude", "precise"):
            assert f'name="{nom}"' in contenu


class TestFormulaireDeRecherche:
    """Une URL partagée ne porte que le libellé, jamais le slug."""

    def test_une_url_partagee_ouvre_la_fiche(self, client):
        """« ?objet=<libellé> » doit mener à la fiche, pas à un formulaire figé.

        Le libellé est un terme de recherche, pas un titre de fiche :
        « Téléphone mobile » mène à « Téléphones, tablettes ou consoles ».
        """
        from unit_tests.qfdmd.qfdmod_factory import ProduitPageFactory

        fiche = ProduitPageFactory(parent=None)
        # La fabrique crée déjà le terme de recherche de la fiche (relation
        # un-à-un) : on le renomme plutôt que d'en ajouter un second.
        terme = ProduitPageSearchTerm.objects.get(produit_page=fiche)
        terme.searchable_title = "Bidule test"
        terme.save()

        reponse = client.get(
            reverse("assistant:recherche"), {"objet": "Bidule test", "adresse": "Auray"}
        )

        assert reponse.status_code == 302
        assert reponse.url.startswith(
            reverse("assistant:produit", kwargs={"slug": fiche.slug})
        )

    def test_la_fiche_explicite_prime_sur_le_libelle(self, client, fiche):
        """L'autocomplétion a déjà tranché : ne pas refaire la résolution."""
        reponse = client.get(
            reverse("assistant:recherche"),
            {"objet": "peu importe", "fiche": fiche.slug, "adresse": "Auray"},
        )

        assert reponse.url.startswith(
            reverse("assistant:produit", kwargs={"slug": fiche.slug})
        )

    def test_un_objet_inconnu_affiche_une_erreur(self, client):
        """Rediriger en silence laissait l'usager devant un formulaire rempli
        qui refusait d'avancer, sans dire pourquoi."""
        reponse = client.get(
            reverse("assistant:recherche"),
            {"objet": "zzz inexistant", "adresse": "Auray"},
        )

        assert reponse.status_code == 200
        contenu = reponse.content.decode()
        assert "qfa-combobox__erreur" in contenu
        assert 'aria-invalid="true"' in contenu

    def test_une_adresse_manquante_affiche_une_erreur(self, client, fiche):
        reponse = client.get(reverse("assistant:recherche"), {"fiche": fiche.slug})

        assert reponse.status_code == 200
        assert "qfa-combobox__erreur" in reponse.content.decode()

    def test_la_saisie_est_conservee_quand_elle_est_refusee(self, client):
        contenu = client.get(
            reverse("assistant:recherche"),
            {"objet": "zzz inexistant", "adresse": "Auray"},
        ).content.decode()

        assert 'value="zzz inexistant"' in contenu
        assert 'value="Auray"' in contenu
