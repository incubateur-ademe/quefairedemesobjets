import pytest
from django.urls import reverse

from assistant.consignes import ORDRE_GESTES, consignes_pour
from assistant.parcours import Parcours
from unit_tests.qfdmd.qfdmod_factory import ProduitPageFactory
from unit_tests.qfdmo.action_factory import GroupeActionFactory

pytestmark = pytest.mark.django_db

LIBELLES_COURTS = {
    "reparer": "Réparer",
    "donner_echanger_rapporter": "Donner",
    "emprunter_preter_louer": "Prêter",
    "vendre_acheter": "Vendre",
    "trier": "Déposer",
}


@pytest.fixture(autouse=True)
def gestes():
    """Les cinq groupes, comme la fixture `actions.json` les fournit en prod."""
    return [
        GroupeActionFactory(code=code, libelle_court=libelle)
        for code, libelle in LIBELLES_COURTS.items()
    ]


class TestConsignes:
    def test_hierarchie_reparable_bon_etat_hors_usage(self):
        """L'ordre d'affichage est imposé par #3295, pas laissé à la base."""
        codes = [consigne["geste"] for consigne in consignes_pour(None)]

        assert codes == list(ORDRE_GESTES)
        assert codes[0] == "reparer"
        assert codes[-1] == "trier"

    def test_seule_la_reparation_porte_le_bonus(self):
        conditions = {
            consigne["geste"]: {badge["condition"] for badge in consigne["badges"]}
            for consigne in consignes_pour(None)
        }

        assert "bonus" in conditions["reparer"]
        assert all(
            "bonus" not in badges
            for geste, badges in conditions.items()
            if geste != "reparer"
        )

    def test_les_etats_suivent_la_spec(self):
        etats = {
            consigne["geste"]: consigne["badges"][0]["condition"]
            for consigne in consignes_pour(None)
        }

        assert etats["reparer"] == "reparable"
        assert etats["donner_echanger_rapporter"] == "bon_etat"
        assert etats["trier"] == "mauvais_etat"

    def test_chaque_geste_a_une_consigne_non_vide(self):
        assert all(consigne["consigne"].strip() for consigne in consignes_pour(None))

    def test_les_libelles_viennent_de_la_base(self):
        libelles = {c["geste"]: c["libelle"] for c in consignes_pour(None)}

        assert libelles["reparer"] == "Réparer"
        assert libelles["trier"] == "Déposer"

    def test_le_parcours_suit_dans_l_appel_a_l_action(self):
        parcours = Parcours(objet="Chaise", adresse="Auray", longitude=-2.9)

        premiere = consignes_pour(None, parcours)[0]

        assert premiere["url"].startswith(reverse("assistant:solutions"))
        assert "objet=Chaise" in premiere["url"]
        assert "geste=reparer" in premiere["url"]

    def test_sans_parcours_l_appel_a_l_action_reste_valide(self):
        premiere = consignes_pour(None)[0]

        assert premiere["url"] == f"{reverse('assistant:solutions')}?geste=reparer"


class TestFicheObjet:
    @pytest.fixture
    def fiche(self):
        return ProduitPageFactory(parent=None)

    def test_la_fiche_affiche_les_cinq_gestes(self, client, fiche):
        contenu = client.get(
            reverse("assistant:produit", args=[fiche.slug])
        ).content.decode()

        for geste in ORDRE_GESTES:
            assert f'data-geste="{geste}"' in contenu

    def test_l_entete_rappelle_la_recherche(self, client, fiche):
        contenu = client.get(
            reverse("assistant:produit", args=[fiche.slug]),
            {"objet": "Chaise", "adresse": "Auray"},
        ).content.decode()

        assert 'value="Chaise"' in contenu
        assert 'value="Auray"' in contenu

    def test_le_frame_permet_de_changer_d_objet_sans_recharger(self, client, fiche):
        contenu = client.get(
            reverse("assistant:produit", args=[fiche.slug])
        ).content.decode()

        assert 'id="assistant-fiche"' in contenu
        # Pas de bouton sur cette maquette : choisir une suggestion soumet.
        assert "assistant-soumission#soumettre" in contenu


class TestReponseDeFrame:
    """Le gabarit de frame doit rendre le contenu, pas une page vide.

    `ui/layout/turbo.html` déclarait `{% block content %}` quand les pages
    définissent `main` : toute réponse à un Turbo Frame sortait vide, et le
    navigateur retombait sur un rechargement complet.
    """

    def test_la_reponse_de_frame_contient_la_fiche(self, client):
        fiche = ProduitPageFactory(parent=None)

        reponse = client.get(
            reverse("assistant:produit", args=[fiche.slug]),
            headers={"turbo-frame": "assistant-fiche"},
        )

        contenu = reponse.content.decode()
        assert 'id="assistant-fiche"' in contenu
        assert "qfa-bloc-geste" in contenu

    def test_la_reponse_de_frame_omet_le_layout(self, client):
        """Sinon Turbo transfère un document entier pour n'en garder qu'un bout."""
        fiche = ProduitPageFactory(parent=None)

        contenu = client.get(
            reverse("assistant:produit", args=[fiche.slug]),
            headers={"turbo-frame": "assistant-fiche"},
        ).content.decode()

        assert "<!DOCTYPE html>" not in contenu.upper()


class TestLiensSortantDuFrame:
    """Un lien enfermé dans un frame doit dire quand il en sort.

    Le CTA vit dans `assistant-fiche` : sans `_top`, Turbo cherche un frame de
    ce nom dans l'écran solutions, qui est une page entière et n'en contient
    aucun. Le résultat est un « Content missing » à la place de la carte.
    """

    def test_le_cta_des_gestes_sort_du_frame(self, client):
        fiche = ProduitPageFactory(parent=None)

        contenu = client.get(
            reverse("assistant:produit", args=[fiche.slug])
        ).content.decode()

        assert 'data-turbo-frame="_top"' in contenu

    def test_l_ecran_solutions_n_a_pas_le_frame_de_la_fiche(self, client):
        """C'est ce qui rend `_top` nécessaire : le vérifier fige le lien."""
        contenu = client.get(
            reverse("assistant:solutions"), {"geste": "reparer"}
        ).content.decode()

        assert 'id="assistant-fiche"' not in contenu
