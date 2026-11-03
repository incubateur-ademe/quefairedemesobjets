import json

import pytest
from django.urls import reverse

from assistant.consignes import BLOCKS, consignes_for
from assistant.parcours import Parcours
from qfdmd.models import LieuDeDepot
from qfdmo.models.action import Action, GroupeAction
from unit_tests.assistant.helpers import field, html_of, query_of
from unit_tests.qfdmd.helpers import consigne, grid, page_with
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


def fiche_avec_carte(**kwargs):
    """A fiche as most live ones: its body holds the map."""
    body = [{"type": "carte", "id": "carte", "value": {"carte_config": None}}]
    return ProduitPageFactory(body=json.dumps(body), parent=None, **kwargs)


def bloc_buttons(page):
    return page.select("article.qfa-bloc-geste a.qfa-bouton")


class TestConsignes:
    def test_the_static_blocks_follow_the_spec(self):
        """Order, labels, gestes and badges of the three blocks: repairable,
        good condition, out of use. "Donner ou revendre" spans two gestes."""
        consignes = consignes_for(None)

        assert [
            (
                c["code"],
                c["libelle"],
                c["gestes"],
                [badge["condition"] for badge in c["badges"]],
            )
            for c in consignes
        ] == [
            ("reparer", "Réparer", ["reparer"], ["reparable", "bonus"]),
            (
                "donner_revendre",
                "Donner ou revendre",
                ["donner_echanger_rapporter", "vendre_acheter"],
                ["bon_etat"],
            ),
            ("trier", "Déposer", ["trier"], ["mauvais_etat"]),
        ]
        assert all(c["consigne"].strip() for c in consignes)

    def test_a_block_skips_the_gestes_missing_from_the_database(self):
        GroupeAction.objects.filter(code="vendre_acheter").delete()

        blocks = {c["code"]: c for c in consignes_for(None)}

        assert blocks["donner_revendre"]["gestes"] == ["donner_echanger_rapporter"]

    def test_the_parcours_follows_in_the_call_to_action(self):
        parcours = Parcours(objet="Chaise", adresse="Auray", longitude=-2.9)

        first = consignes_for(None, parcours)[0]

        assert first["url"].startswith(reverse("assistant:solutions"))
        assert query_of(first["url"])["objet"] == ["Chaise"]
        assert query_of(first["url"])["geste"] == ["reparer"]

    def test_without_parcours_the_call_to_action_stays_valid(self):
        first = consignes_for(None)[0]

        assert first["url"] == f"{reverse('assistant:solutions')}?geste=reparer"

    def test_a_two_geste_block_repeats_geste_in_its_link(self):
        donner = consignes_for(None)[1]

        assert donner["url"].endswith(
            "?geste=donner_echanger_rapporter&geste=vendre_acheter"
        )

    def test_the_link_carries_the_fiche_slug_when_known(self, fiche):
        first = consignes_for(fiche, Parcours(objet="Chaise"))[0]

        assert query_of(first["url"])["fiche"] == [fiche.slug]


class TestFicheObjet:
    @pytest.fixture
    def fiche(self):
        return fiche_avec_carte()

    def test_the_fiche_shows_the_three_blocks(self, client, fiche):
        page = html_of(client.get(reverse("assistant:produit", args=[fiche.slug])))

        assert [
            article["data-gestes"] for article in page.select("article.qfa-bloc-geste")
        ] == [" ".join(block["gestes"]) for block in BLOCKS]

    def test_the_buttons_lead_to_the_solutions(self, client, fiche):
        url = reverse("assistant:produit", args=[fiche.slug])
        page = html_of(client.get(url, {"objet": "Chaise"}))

        assert bloc_buttons(page)
        for button in bloc_buttons(page):
            assert button["href"].startswith(reverse("assistant:solutions"))
            assert button.get_text(strip=True) == "Je découvre les solutions"

    def test_a_fiche_without_map_has_no_button(self, client):
        """Véhicule hors d'usage: no map on the site, so no solution to show."""
        fiche = ProduitPageFactory(parent=None)
        url = reverse("assistant:produit", args=[fiche.slug])
        solutions = reverse("assistant:solutions")

        for params in ({}, {"longitude": "-0.56", "latitude": "47.47"}):
            page = html_of(client.get(url, {"objet": "Véhicule", **params}))
            assert page.select("article.qfa-bloc-geste")
            assert page.select(f'a[href^="{solutions}?"]') == []
        assert all(c["sans_carte"] for c in consignes_for(fiche))
        assert not any(c["sans_carte"] for c in consignes_for(fiche_avec_carte()))

    def test_the_header_recalls_the_search(self, client, fiche):
        page = html_of(
            client.get(
                reverse("assistant:produit", args=[fiche.slug]),
                {"objet": "Chaise", "adresse": "Auray"},
            )
        )

        assert field(page, "objet")["value"] == "Chaise"
        assert field(page, "adresse")["value"] == "Auray"

    def test_without_a_search_the_header_shows_the_fiche(self, client, fiche):
        """An embed's `data-objet` lands here without a typed label."""
        page = html_of(client.get(reverse("assistant:produit", args=[fiche.slug])))

        assert field(page, "objet")["value"] == fiche.title

    def test_choosing_a_suggestion_submits_inside_the_frame(self, client, fiche):
        """No button on this screen: choosing a suggestion submits the form,
        and the frame swaps the fiche without a reload."""
        page = html_of(client.get(reverse("assistant:produit", args=[fiche.slug])))

        form = page.select_one("turbo-frame#assistant-fiche form")
        assert "assistant-submit#submit" in form["data-action"]

    def test_the_gestes_cta_leaves_the_frame(self, client, fiche):
        """Without `_top`, Turbo looks for the `assistant-fiche` frame in the
        solutions screen, which has none, and shows "Content missing"."""
        page = html_of(client.get(reverse("assistant:produit", args=[fiche.slug])))

        assert bloc_buttons(page)
        for button in bloc_buttons(page):
            assert button["data-turbo-frame"] == "_top"


class TestFrameResponse:
    """The frame template must render the page's `main` block, else every
    Turbo Frame response is empty and the browser falls back on a reload."""

    def test_the_frame_response_contains_the_fiche(self, client, fiche):
        page = html_of(
            client.get(
                reverse("assistant:produit", args=[fiche.slug]),
                headers={"turbo-frame": "assistant-fiche"},
            )
        )

        assert page.select("turbo-frame#assistant-fiche article.qfa-bloc-geste")

    def test_the_frame_response_omits_the_layout(self, client, fiche):
        """Otherwise Turbo transfers a whole document to keep one piece of it."""
        content = client.get(
            reverse("assistant:produit", args=[fiche.slug]),
            headers={"turbo-frame": "assistant-fiche"},
        ).content.decode()

        assert "<!DOCTYPE html>" not in content.upper()

    def test_the_solutions_screen_has_no_fiche_frame(self, client):
        """This is what makes `_top` necessary on the fiche's CTA."""
        page = html_of(client.get(reverse("assistant:solutions"), {"geste": "reparer"}))

        assert page.select_one("#assistant-fiche") is None


class TestConsignesFromTheCms:
    """Once a fiche carries a grid of consignes, the static text gives way to
    the CMS content."""

    @pytest.fixture
    def fiche(self):
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
                consigne("Au bac", block_id="bac", lieu_de_depot=bac.pk, gestes=["trier"]),
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
        assert html_of(str(consignes[2]["consigne"])).p.get_text() == "Au bac"

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


class TestConsigneLinks:
    """The consigne's links live in the fiche frame: left as is, Turbo shows
    "Content missing"."""

    def consigne_link(self, contenu, parcours=None):
        fiche = page_with(grid(consigne("Au bac", contenu=contenu, gestes=["trier"])))
        return html_of(str(consignes_for(fiche, parcours)[0]["consigne"])).a

    def test_a_link_to_a_fiche_opens_it_in_the_assistant(self):
        cible = ProduitPageFactory(title="Bouteille", slug="bouteille")
        parcours = Parcours.from_query(
            {"adresse": "Nantes", "longitude": "-1.55", "latitude": "47.21"}
        )

        link = self.consigne_link(
            f'<p><a linktype="page" id="{cible.id}">bouteilles</a></p>', parcours
        )

        assert link["href"].startswith(reverse("assistant:produit", args=["bouteille"]))
        query = query_of(link["href"])
        assert query["fiche"] == ["bouteille"]
        assert query["objet"] == ["Bouteille"]
        assert query["adresse"] == ["Nantes"]
        assert link["data-turbo-frame"] == "_top"

    def test_any_other_link_opens_in_a_new_tab(self):
        link = self.consigne_link('<p><a href="https://example.org">ailleurs</a></p>')

        assert link["target"] == "_blank"
        assert link["data-turbo-frame"] == "_top"
