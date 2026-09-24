import pytest
from django.urls import reverse

from unit_tests.qfdmo.action_factory import GroupeActionFactory

pytestmark = pytest.mark.django_db


@pytest.fixture
def reparer():
    return GroupeActionFactory(
        code="reparer", libelle_court="Réparer", couleur="#009081"
    )


class TestSolutionsScreen:
    def test_the_map_receives_the_geste_and_the_position(self, client, reparer):
        content = client.get(
            reverse("assistant:solutions"),
            {"geste": "reparer", "longitude": "2.36", "latitude": "48.85"},
        ).content.decode()

        assert 'data-assistant-carte-geste-value="reparer"' in content
        assert 'data-assistant-carte-longitude-value="2.36"' in content

    def test_the_red_marker_only_shows_for_a_precise_address(self, client, reparer):
        """ "Lyon" has no position to show (#3356 §4)."""
        municipality = client.get(
            reverse("assistant:solutions"),
            {"geste": "reparer", "longitude": "4.83", "latitude": "45.75"},
        ).content.decode()
        address = client.get(
            reverse("assistant:solutions"),
            {
                "geste": "reparer",
                "longitude": "2.36",
                "latitude": "48.85",
                "precise": "true",
            },
        ).content.decode()

        assert 'precise-address-value="false"' in municipality
        assert 'precise-address-value="true"' in address

    def test_without_position_the_map_still_has_a_center(self, client, reparer):
        """Otherwise MapLibre receives NaN and refuses to initialize."""
        content = client.get(
            reverse("assistant:solutions"), {"geste": "reparer"}
        ).content.decode()

        assert 'longitude-value=""' not in content

    def test_the_geste_is_recalled_in_the_back_button(self, client, reparer):
        from unit_tests.qfdmd.qfdmod_factory import ProduitPageFactory

        fiche = ProduitPageFactory(parent=None)
        content = client.get(
            reverse("assistant:solutions"), {"geste": "reparer", "fiche": fiche.slug}
        ).content.decode()

        assert "Réparer" in content
        assert reverse("assistant:produit", args=[fiche.slug]) in content

    def test_going_back_finds_the_fiche_from_the_label(self, client, reparer):
        """A shared URL often carries only the label.

        Sending the user to the home page would make them redo the search they
        just did.
        """
        from qfdmd.models import ProduitPageSearchTerm
        from unit_tests.qfdmd.qfdmod_factory import ProduitPageFactory

        fiche = ProduitPageFactory(parent=None)
        term = ProduitPageSearchTerm.objects.get(produit_page=fiche)
        term.searchable_title = "Bidule test"
        term.save()

        content = client.get(
            reverse("assistant:solutions"),
            {"geste": "reparer", "objet": "Bidule test"},
        ).content.decode()

        assert reverse("assistant:produit", args=[fiche.slug]) in content

    def test_the_explicit_fiche_wins_over_the_label(self, client, reparer):
        from unit_tests.qfdmd.qfdmod_factory import ProduitPageFactory

        fiche = ProduitPageFactory(parent=None)

        content = client.get(
            reverse("assistant:solutions"),
            {"geste": "reparer", "fiche": fiche.slug, "objet": "peu importe"},
        ).content.decode()

        assert reverse("assistant:produit", args=[fiche.slug]) in content

    def test_the_back_link_does_not_repeat_the_slug(self, client, reparer):
        """The fiche's path already carries it."""
        from unit_tests.qfdmd.qfdmod_factory import ProduitPageFactory

        fiche = ProduitPageFactory(parent=None)

        content = client.get(
            reverse("assistant:solutions"), {"geste": "reparer", "fiche": fiche.slug}
        ).content.decode()

        assert f"fiche={fiche.slug}" not in content.split("qfa-carte")[0]

    def test_without_objet_going_back_leads_to_the_home_page(self, client, reparer):
        """Better the home page than a dead link to an unknown fiche."""
        content = client.get(
            reverse("assistant:solutions"), {"geste": "reparer"}
        ).content.decode()

        assert f'href="{reverse("assistant:home")}?' in content

    def test_the_pins_link_carries_the_parcours(self, client, reparer):
        """Without it, "Revenir aux solutions" would lose geste and address."""
        from unit_tests.qfdmd.qfdmod_factory import ProduitPageFactory

        fiche = ProduitPageFactory(parent=None)
        content = client.get(
            reverse("assistant:solutions"),
            {"geste": "reparer", "fiche": fiche.slug, "adresse": "Auray"},
        ).content.decode()

        assert "lieu-url-value" in content
        assert "geste%3Dreparer" in content or "geste=reparer" in content

    def test_the_lieu_page_leads_back_to_the_same_solutions(self, client, reparer):
        """Round trip: solutions -> pin link -> lieu page -> back link.

        The pin link and the back link must speak the same vocabulary: with
        `fiche` sent one way and `slug` read the other, the objet was lost on
        the way back.
        """
        import re
        from html import unescape

        from unit_tests.qfdmd.qfdmod_factory import ProduitPageFactory
        from unit_tests.qfdmo.acteur_factory import DisplayedActeurFactory

        fiche = ProduitPageFactory(parent=None)
        lieu = DisplayedActeurFactory()
        solutions = client.get(
            reverse("assistant:solutions"),
            {"geste": "reparer", "fiche": fiche.slug, "adresse": "Auray"},
        ).content.decode()
        pin_url = unescape(re.search(r'lieu-url-value="([^"]+)"', solutions)[1])

        lieu_page = client.get(pin_url.replace("__uuid__", lieu.uuid)).content.decode()
        back = unescape(re.search(r'href="([^"]*solutions[^"]*)"', lieu_page)[1])

        assert f"fiche={fiche.slug}" in back
        assert "geste=reparer" in back
        assert "adresse=Auray" in back

    def test_a_block_of_two_gestes_shows_both_icons_and_its_label(
        self, client, reparer
    ):
        """ "Donner ou revendre" (30174:11559) spans two GroupeAction."""
        GroupeActionFactory(code="donner_echanger_rapporter", libelle_court="Donner")
        GroupeActionFactory(code="vendre_acheter", libelle_court="Vendre")

        content = client.get(
            reverse("assistant:solutions"),
            {"geste": ["donner_echanger_rapporter", "vendre_acheter"]},
        ).content.decode()

        assert "Donner ou revendre" in content
        assert 'data-geste="donner_echanger_rapporter"' in content
        assert 'data-geste="vendre_acheter"' in content
        assert (
            'data-assistant-carte-geste-value="donner_echanger_rapporter,vendre_acheter"'
            in content
        )
        assert content.count('name="geste"') == 2

    def test_the_accessible_list_carries_the_nearest_places(self, client, reparer):
        """The map fetches its own places; the server-rendered list is the
        only path to the results without it."""
        from django.contrib.gis.geos import Point

        from unit_tests.qfdmo.acteur_factory import (
            DisplayedActeurFactory,
            DisplayedPropositionServiceFactory,
        )
        from unit_tests.qfdmo.action_factory import ActionFactory

        action = ActionFactory(code="reparer", groupe_action=reparer)
        lieu = DisplayedActeurFactory(
            nom="Atelier test", location=Point(2.36, 48.85, srid=4326)
        )
        DisplayedPropositionServiceFactory(acteur=lieu, action=action)

        content = client.get(
            reverse("assistant:solutions"),
            {"geste": "reparer", "longitude": "2.36", "latitude": "48.85"},
        ).content.decode()

        assert "Atelier test" in content
        assert "Aucun lieu à proximité" not in content

    def test_the_map_canvas_is_a_permanent_element_inside_the_map(
        self, client, reparer
    ):
        """Turbo carries the canvas from screen to screen; here it lives in
        the map component, not parked at the end of the body."""
        content = client.get(
            reverse("assistant:solutions"), {"geste": "reparer"}
        ).content.decode()

        assert content.count('id="assistant-carte-canvas"') == 1
        assert content.count("data-turbo-permanent") == 1
        assert "qfa-carte__canvas" in content
