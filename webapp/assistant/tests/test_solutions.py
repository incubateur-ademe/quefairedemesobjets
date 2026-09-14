import pytest
from django.urls import reverse

from unit_tests.qfdmo.action_factory import GroupeActionFactory

pytestmark = pytest.mark.django_db


@pytest.fixture
def reparer():
    return GroupeActionFactory(
        code="reparer", libelle_court="Réparer", couleur="#009081"
    )


class TestEcranSolutions:
    def test_la_carte_recoit_le_geste_et_la_position(self, client, reparer):
        contenu = client.get(
            reverse("assistant:solutions"),
            {"geste": "reparer", "longitude": "2.36", "latitude": "48.85"},
        ).content.decode()

        assert 'data-assistant-carte-geste-value="reparer"' in contenu
        assert 'data-assistant-carte-longitude-value="2.36"' in contenu

    def test_la_punaise_rouge_n_apparait_que_pour_une_adresse_precise(
        self, client, reparer
    ):
        """« Lyon » n'a pas de position à montrer (#3356 §4)."""
        commune = client.get(
            reverse("assistant:solutions"),
            {"geste": "reparer", "longitude": "4.83", "latitude": "45.75"},
        ).content.decode()
        adresse = client.get(
            reverse("assistant:solutions"),
            {
                "geste": "reparer",
                "longitude": "2.36",
                "latitude": "48.85",
                "precise": "true",
            },
        ).content.decode()

        assert 'adresse-precise-value="false"' in commune
        assert 'adresse-precise-value="true"' in adresse

    def test_sans_position_la_carte_a_tout_de_meme_un_centre(self, client, reparer):
        """Sinon MapLibre reçoit NaN et refuse de s'initialiser."""
        contenu = client.get(
            reverse("assistant:solutions"), {"geste": "reparer"}
        ).content.decode()

        assert 'longitude-value=""' not in contenu

    def test_le_geste_est_rappele_dans_le_bouton_de_retour(self, client, reparer):
        from unit_tests.qfdmd.qfdmod_factory import ProduitPageFactory

        fiche = ProduitPageFactory(parent=None)
        contenu = client.get(
            reverse("assistant:solutions"), {"geste": "reparer", "fiche": fiche.slug}
        ).content.decode()

        assert "Réparer" in contenu
        assert reverse("assistant:produit", args=[fiche.slug]) in contenu

    def test_le_retour_retrouve_la_fiche_depuis_le_libelle(self, client, reparer):
        """Une URL partagée ne porte souvent que le libellé.

        Renvoyer alors vers l'accueil ferait refaire à l'usager la recherche
        qu'il vient de faire.
        """
        from unit_tests.qfdmd.qfdmod_factory import ProduitPageFactory
        from qfdmd.models import ProduitPageSearchTerm

        fiche = ProduitPageFactory(parent=None)
        terme = ProduitPageSearchTerm.objects.get(produit_page=fiche)
        terme.searchable_title = "Bidule test"
        terme.save()

        contenu = client.get(
            reverse("assistant:solutions"),
            {"geste": "reparer", "objet": "Bidule test"},
        ).content.decode()

        assert reverse("assistant:produit", args=[fiche.slug]) in contenu

    def test_la_fiche_explicite_prime_sur_le_libelle(self, client, reparer):
        from unit_tests.qfdmd.qfdmod_factory import ProduitPageFactory

        fiche = ProduitPageFactory(parent=None)

        contenu = client.get(
            reverse("assistant:solutions"),
            {"geste": "reparer", "fiche": fiche.slug, "objet": "peu importe"},
        ).content.decode()

        assert reverse("assistant:produit", args=[fiche.slug]) in contenu

    def test_l_ancien_parametre_slug_reste_accepte(self, client, reparer):
        """Des liens portant `slug=` ont pu être partagés avant le renommage."""
        from unit_tests.qfdmd.qfdmod_factory import ProduitPageFactory

        fiche = ProduitPageFactory(parent=None)

        contenu = client.get(
            reverse("assistant:solutions"), {"geste": "reparer", "slug": fiche.slug}
        ).content.decode()

        assert reverse("assistant:produit", args=[fiche.slug]) in contenu

    def test_sans_objet_le_retour_mene_a_l_accueil(self, client, reparer):
        """Mieux vaut l'accueil qu'un lien mort vers une fiche inconnue."""
        contenu = client.get(
            reverse("assistant:solutions"), {"geste": "reparer"}
        ).content.decode()

        assert f'href="{reverse("assistant:home")}?' in contenu

    def test_le_lien_des_punaises_emporte_le_parcours(self, client, reparer):
        """Sans lui, « Revenir aux solutions » perdrait geste et adresse."""
        from unit_tests.qfdmd.qfdmod_factory import ProduitPageFactory

        fiche = ProduitPageFactory(parent=None)
        contenu = client.get(
            reverse("assistant:solutions"),
            {"geste": "reparer", "fiche": fiche.slug, "adresse": "Auray"},
        ).content.decode()

        assert "url-lieu-value" in contenu
        assert "geste%3Dreparer" in contenu or "geste=reparer" in contenu
