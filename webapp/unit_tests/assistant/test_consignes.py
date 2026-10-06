import pytest
from django.urls import reverse

from assistant.consignes import GESTES_ORDER, consignes_for
from assistant.parcours import Parcours
from unit_tests.qfdmd.qfdmod_factory import ProduitPageFactory
from unit_tests.qfdmo.action_factory import GroupeActionFactory

pytestmark = pytest.mark.django_db

SHORT_LABELS = {
    "reparer": "Réparer",
    "donner_echanger_rapporter": "Donner",
    "emprunter_preter_louer": "Prêter",
    "vendre_acheter": "Vendre",
    "trier": "Déposer",
}


@pytest.fixture(autouse=True)
def gestes():
    """The five groupes, as the `actions.json` fixture provides them in prod."""
    return [
        GroupeActionFactory(code=code, libelle_court=label)
        for code, label in SHORT_LABELS.items()
    ]


class TestConsignes:
    def test_hierarchy_repairable_good_out_of_use(self):
        """The display order is imposed by #3295, not left to the database."""
        codes = [consigne["geste"] for consigne in consignes_for(None)]

        assert codes == list(GESTES_ORDER)
        assert codes[0] == "reparer"
        assert codes[-1] == "trier"

    def test_only_repair_carries_the_bonus(self):
        conditions = {
            consigne["geste"]: {badge["condition"] for badge in consigne["badges"]}
            for consigne in consignes_for(None)
        }

        assert "bonus" in conditions["reparer"]
        assert all(
            "bonus" not in badges
            for geste, badges in conditions.items()
            if geste != "reparer"
        )

    def test_conditions_follow_the_spec(self):
        etats = {
            consigne["geste"]: consigne["badges"][0]["condition"]
            for consigne in consignes_for(None)
        }

        assert etats["reparer"] == "reparable"
        assert etats["donner_echanger_rapporter"] == "bon_etat"
        assert etats["trier"] == "mauvais_etat"

    def test_every_geste_has_a_non_empty_consigne(self):
        assert all(consigne["consigne"].strip() for consigne in consignes_for(None))

    def test_labels_come_from_the_database(self):
        labels = {c["geste"]: c["libelle"] for c in consignes_for(None)}

        assert labels["reparer"] == "Réparer"
        assert labels["trier"] == "Déposer"

    def test_the_parcours_follows_in_the_call_to_action(self):
        parcours = Parcours(objet="Chaise", adresse="Auray", longitude=-2.9)

        first = consignes_for(None, parcours)[0]

        assert first["url"].startswith(reverse("assistant:solutions"))
        assert "objet=Chaise" in first["url"]
        assert "geste=reparer" in first["url"]

    def test_without_parcours_the_call_to_action_stays_valid(self):
        first = consignes_for(None)[0]

        assert first["url"] == f"{reverse('assistant:solutions')}?geste=reparer"


class TestFicheObjet:
    @pytest.fixture
    def fiche(self):
        return ProduitPageFactory(parent=None)

    def test_the_fiche_shows_the_five_gestes(self, client, fiche):
        content = client.get(
            reverse("assistant:produit", args=[fiche.slug])
        ).content.decode()

        for geste in GESTES_ORDER:
            assert f'data-geste="{geste}"' in content

    def test_the_header_recalls_the_search(self, client, fiche):
        content = client.get(
            reverse("assistant:produit", args=[fiche.slug]),
            {"objet": "Chaise", "adresse": "Auray"},
        ).content.decode()

        assert 'value="Chaise"' in content
        assert 'value="Auray"' in content

    def test_the_frame_allows_changing_objet_without_reload(self, client, fiche):
        content = client.get(
            reverse("assistant:produit", args=[fiche.slug])
        ).content.decode()

        assert 'id="assistant-fiche"' in content
        # No button on this mockup: choosing a suggestion submits.
        assert "assistant-submit#submit" in content


class TestFrameResponse:
    """The frame template must render the content, not an empty page.

    `ui/layout/turbo.html` declared `{% block content %}` while the pages
    define `main`: every response to a Turbo Frame came out empty, and the
    browser fell back on a full reload.
    """

    def test_the_frame_response_contains_the_fiche(self, client):
        fiche = ProduitPageFactory(parent=None)

        response = client.get(
            reverse("assistant:produit", args=[fiche.slug]),
            headers={"turbo-frame": "assistant-fiche"},
        )

        content = response.content.decode()
        assert 'id="assistant-fiche"' in content
        assert "qfa-bloc-geste" in content

    def test_the_frame_response_omits_the_layout(self, client):
        """Otherwise Turbo transfers a whole document to keep one piece of it."""
        fiche = ProduitPageFactory(parent=None)

        content = client.get(
            reverse("assistant:produit", args=[fiche.slug]),
            headers={"turbo-frame": "assistant-fiche"},
        ).content.decode()

        assert "<!DOCTYPE html>" not in content.upper()


class TestLinksLeavingTheFrame:
    """A link enclosed in a frame must say when it leaves it.

    The CTA lives in `assistant-fiche`: without `_top`, Turbo looks for a frame
    of that name in the solutions screen, which is a full page and has none.
    The result is a "Content missing" instead of the map.
    """

    def test_the_gestes_cta_leaves_the_frame(self, client):
        fiche = ProduitPageFactory(parent=None)

        content = client.get(
            reverse("assistant:produit", args=[fiche.slug])
        ).content.decode()

        assert 'data-turbo-frame="_top"' in content

    def test_the_solutions_screen_has_no_fiche_frame(self, client):
        """This is what makes `_top` necessary: checking it pins the link."""
        content = client.get(
            reverse("assistant:solutions"), {"geste": "reparer"}
        ).content.decode()

        assert 'id="assistant-fiche"' not in content
