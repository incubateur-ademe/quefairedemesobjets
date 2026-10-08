import pytest
from django.urls import reverse

from assistant.consignes import BLOCKS, consignes_for
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
        codes = [consigne["code"] for consigne in consignes_for(None)]

        assert codes == ["reparer", "donner_revendre", "trier"]

    def test_the_fiche_has_the_three_blocks_of_the_mockup(self):
        """Figma 30139:14476: "Donner ou revendre" spans two gestes."""
        blocks = {c["code"]: c for c in consignes_for(None)}

        assert len(blocks) == 3
        assert blocks["donner_revendre"]["gestes"] == [
            "donner_echanger_rapporter",
            "vendre_acheter",
        ]
        assert blocks["donner_revendre"]["libelle"] == "Donner ou revendre"

    def test_a_block_skips_the_gestes_missing_from_the_database(self):
        from qfdmo.models.action import GroupeAction

        GroupeAction.objects.filter(code="vendre_acheter").delete()

        blocks = {c["code"]: c for c in consignes_for(None)}

        assert blocks["donner_revendre"]["gestes"] == ["donner_echanger_rapporter"]

    def test_only_repair_carries_the_bonus(self):
        conditions = {
            consigne["code"]: {badge["condition"] for badge in consigne["badges"]}
            for consigne in consignes_for(None)
        }

        assert "bonus" in conditions["reparer"]
        assert all(
            "bonus" not in badges
            for code, badges in conditions.items()
            if code != "reparer"
        )

    def test_conditions_follow_the_spec(self):
        etats = {
            consigne["code"]: consigne["badges"][0]["condition"]
            for consigne in consignes_for(None)
        }

        assert etats["reparer"] == "reparable"
        assert etats["donner_revendre"] == "bon_etat"
        assert etats["trier"] == "mauvais_etat"

    def test_every_geste_has_a_non_empty_consigne(self):
        assert all(consigne["consigne"].strip() for consigne in consignes_for(None))

    def test_labels_are_those_of_the_mockup(self):
        labels = [c["libelle"] for c in consignes_for(None)]

        assert labels == ["Réparer", "Donner ou revendre", "Déposer"]

    def test_the_parcours_follows_in_the_call_to_action(self):
        parcours = Parcours(objet="Chaise", adresse="Auray", longitude=-2.9)

        first = consignes_for(None, parcours)[0]

        assert first["url"].startswith(reverse("assistant:solutions"))
        assert "objet=Chaise" in first["url"]
        assert "geste=reparer" in first["url"]

    def test_without_parcours_the_call_to_action_stays_valid(self):
        first = consignes_for(None)[0]

        assert first["url"] == f"{reverse('assistant:solutions')}?geste=reparer"

    def test_a_two_geste_block_repeats_geste_in_its_link(self):
        donner = consignes_for(None)[1]

        assert donner["url"].endswith(
            "?geste=donner_echanger_rapporter&geste=vendre_acheter"
        )


class TestFicheObjet:
    @pytest.fixture
    def fiche(self):
        return ProduitPageFactory(parent=None)

    def test_the_fiche_shows_the_three_blocks(self, client, fiche):
        content = client.get(
            reverse("assistant:produit", args=[fiche.slug])
        ).content.decode()

        for block in BLOCKS:
            assert f'data-gestes="{" ".join(block["gestes"])}"' in content

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


class TestBlockLinks:
    def test_the_link_carries_the_fiche_slug_when_known(self):
        from assistant.consignes import consignes_for
        from assistant.parcours import Parcours

        fiche = ProduitPageFactory(parent=None)
        first = consignes_for(fiche, Parcours(objet="Chaise"))[0]

        assert f"fiche={fiche.slug}" in first["url"]

    def test_the_counter_is_disabled(self):
        located = consignes_for(
            None, Parcours(objet="Chaise", longitude=-0.56, latitude=47.47)
        )[0]

        assert located["url_compte"] == ""

    def test_the_counter_url_needs_a_position(self, monkeypatch):
        monkeypatch.setattr("assistant.consignes.COUNTER_ENABLED", True)
        from assistant.consignes import consignes_for
        from assistant.parcours import Parcours

        without = consignes_for(None, Parcours(objet="Chaise"))[0]
        located = consignes_for(
            None, Parcours(objet="Chaise", longitude=-0.56, latitude=47.47)
        )[0]

        assert without["url_compte"] == ""
        assert located["url_compte"].startswith(reverse("api_v1:lieux-compte"))
        assert "longitude=-0.56" in located["url_compte"]


class TestConsignesFromTheCms:
    """Once a fiche carries a grid of consignes (#3284), the static text
    gives way to the CMS content."""

    @pytest.fixture
    def fiche(self):
        from qfdmd.models import LieuDeDepot
        from unit_tests.qfdmd.test_consignes_block import consigne, grid, page_with

        bac = LieuDeDepot.objects.get(code="bac_de_tri")
        return page_with(
            grid(
                consigne(
                    "Le faire réparer",
                    id="rep",
                    etat="reparable",
                    bonus_reparation=True,
                    gestes=["reparer"],
                ),
                consigne(
                    "Donner ou revendre",
                    id="don",
                    etat="bon_etat",
                    gestes=["donner", "revendre", "echanger"],
                ),
                consigne("Au bac", id="bac", lieu_de_depot=bac.pk, gestes=["trier"]),
            ),
            parent=None,
        )

    def test_the_cms_replaces_the_static_text(self, fiche):
        consignes = consignes_for(fiche)

        assert [c["code"] for c in consignes] == ["rep", "don", "bac"]
        assert [c["libelle"] for c in consignes] == [
            "Le faire réparer",
            "Donner ou revendre",
            "Au bac",
        ]
        assert "<p>Au bac</p>" in str(consignes[2]["consigne"])

    def test_actions_become_groupes_without_repetition(self, fiche):
        """`geste` on the solutions screen is a GroupeAction: donner, revendre
        and echanger fold into two groupes, in the order of the actions."""
        donner = consignes_for(fiche)[1]

        assert donner["gestes"] == ["donner_echanger_rapporter", "vendre_acheter"]
        assert donner["url"].endswith(
            "?fiche="
            + fiche.slug
            + "&geste=donner_echanger_rapporter&geste=vendre_acheter"
        )

    def test_preter_and_louer_stay_out_of_the_mvp(self):
        """A grid edited in the CMS may still list them."""
        from unit_tests.qfdmd.test_consignes_block import consigne, grid, page_with

        page = page_with(
            grid(
                consigne(
                    "Donner",
                    id="don",
                    etat="bon_etat",
                    gestes=["donner", "preter", "louer"],
                )
            ),
            parent=None,
        )

        assert consignes_for(page)[0]["gestes"] == ["donner_echanger_rapporter"]

    def test_badges_follow_the_fields(self, fiche):
        badges = {
            c["code"]: [(b["condition"], b["libelle"]) for b in c["badges"]]
            for c in consignes_for(fiche)
        }

        assert badges["rep"] == [
            ("reparable", "Réparable"),
            ("bonus", "Bonus Réparation"),
        ]
        assert badges["don"] == [("bon_etat", "Bon état")]
        assert badges["bac"] == [("lieu_de_depot", "Bac de tri")]

    def test_a_consigne_whose_actions_have_no_groupe_is_skipped(self):
        from qfdmo.models.action import Action
        from unit_tests.qfdmd.test_consignes_block import consigne, grid, page_with

        Action.objects.filter(code="trier").update(groupe_action=None)
        fiche = page_with(grid(consigne("Orphan", gestes=["trier"])), parent=None)

        assert consignes_for(fiche) == []

    def test_a_fiche_without_grid_keeps_the_static_text(self):
        fiche = ProduitPageFactory(parent=None)

        assert [c["code"] for c in consignes_for(fiche)] == [
            "reparer",
            "donner_revendre",
            "trier",
        ]
