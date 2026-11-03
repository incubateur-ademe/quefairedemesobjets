import pytest
from django.contrib.gis.geos import Point
from django.urls import reverse

from unit_tests.assistant.helpers import (
    error_of,
    field,
    html_of,
    place_offering,
    query_of,
    rename_search_term,
)
from unit_tests.qfdmo.action_factory import GroupeActionFactory

pytestmark = pytest.mark.django_db


def solutions(client, **params):
    return html_of(client.get(reverse("assistant:solutions"), params))


def carte(page):
    return page.select_one('[data-controller="assistant-carte"]')


def accessible_list(page):
    return [
        item.get_text(strip=True)
        for item in page.select(".qfa-carte__accessible-list li")
    ]


def back_link(page):
    return page.select_one("a.qfa-changer-geste")


@pytest.mark.usefixtures("reparer")
class TestSolutionsScreen:
    def test_the_map_receives_the_geste_and_the_position(self, client):
        page = solutions(client, geste="reparer", longitude="2.36", latitude="48.85")

        assert carte(page)["data-assistant-carte-geste-value"] == "reparer"
        assert carte(page)["data-assistant-carte-longitude-value"] == "2.36"

    @pytest.mark.parametrize(
        "params,precise",
        [
            ({"longitude": "4.83", "latitude": "45.75"}, "false"),
            ({"longitude": "2.36", "latitude": "48.85", "precise": "true"}, "true"),
        ],
        ids=["municipality", "address"],
    )
    def test_the_red_marker_only_shows_for_a_precise_address(
        self, client, params, precise
    ):
        """ "Lyon" has no position to show."""
        page = solutions(client, geste="reparer", **params)

        assert carte(page)["data-assistant-carte-precise-address-value"] == precise

    def test_an_address_without_position_is_said_unknown(self, client):
        """Typed without choosing a suggestion: the map falls back on its
        default view, the field says why."""
        page = solutions(client, geste="reparer", adresse="trucmuche")

        assert error_of(page, "adresse").startswith(
            "Nous ne connaissons pas cette adresse"
        )
        assert field(page, "adresse")["aria-invalid"] == "true"

    def test_without_any_address_the_field_asks_for_one(self, client):
        """Geolocation refused or failed: the map shows its default view
        (Paris), which a tester elsewhere took for a broken geolocation."""
        page = solutions(client, geste="reparer")

        assert error_of(page, "adresse").startswith("Saisissez une adresse")

    def test_without_position_the_map_still_has_a_center(self, client):
        """Otherwise MapLibre receives NaN and refuses to initialize."""
        page = solutions(client, geste="reparer")

        assert carte(page)["data-assistant-carte-longitude-value"] != ""
        assert carte(page)["data-assistant-carte-latitude-value"] != ""

    def test_the_geste_is_recalled_in_the_back_button(self, client, fiche):
        page = solutions(client, geste="reparer", fiche=fiche.slug)

        link = back_link(page)
        assert link.get_text(strip=True) == "Réparer"
        assert link["href"].startswith(reverse("assistant:produit", args=[fiche.slug]))

    def test_going_back_finds_the_fiche_from_the_label(self, client, fiche):
        """A shared URL often carries only the label: the home page would make
        the user redo the search they just did."""
        rename_search_term(fiche, "Bidule test")

        page = solutions(client, geste="reparer", objet="Bidule test")

        assert back_link(page)["href"].startswith(
            reverse("assistant:produit", args=[fiche.slug])
        )

    def test_the_explicit_fiche_wins_over_the_label(self, client, fiche):
        page = solutions(client, geste="reparer", fiche=fiche.slug, objet="peu importe")

        assert back_link(page)["href"].startswith(
            reverse("assistant:produit", args=[fiche.slug])
        )

    def test_the_back_link_does_not_repeat_the_slug(self, client, fiche):
        """The fiche's path already carries it."""
        page = solutions(client, geste="reparer", fiche=fiche.slug)

        assert "fiche" not in query_of(back_link(page)["href"])

    def test_without_objet_going_back_leads_to_the_home_page(self, client):
        """Better the home page than a dead link to an unknown fiche."""
        page = solutions(client, geste="reparer")

        assert back_link(page)["href"].startswith(f"{reverse('assistant:home')}?")

    def test_a_block_of_two_gestes_shows_both_icons_and_its_label(self, client):
        """ "Donner ou revendre" spans two GroupeAction."""
        GroupeActionFactory(code="donner_echanger_rapporter", libelle_court="Donner")
        GroupeActionFactory(code="vendre_acheter", libelle_court="Vendre")
        gestes = ["donner_echanger_rapporter", "vendre_acheter"]

        page = solutions(client, geste=gestes)

        link = back_link(page)
        assert link.get_text(strip=True) == "Donner ou revendre"
        assert [
            icon["data-geste"]
            for icon in link.select(".qfa-changer-geste__icones [data-geste]")
        ] == gestes
        assert carte(page)["data-assistant-carte-geste-value"] == ",".join(gestes)
        assert [
            hidden["value"] for hidden in page.select('form input[name="geste"]')
        ] == gestes

    def test_the_accessible_list_carries_the_nearest_places(self, client, reparer):
        """The map fetches its own places; the server-rendered list is the
        only path to the results without it."""
        place_offering(reparer, at=Point(2.36, 48.85, srid=4326), nom="Atelier test")

        page = solutions(client, geste="reparer", longitude="2.36", latitude="48.85")

        assert accessible_list(page) == ["Atelier test"]

    def test_an_unknown_fiche_narrows_no_place(self, client, reparer):
        place_offering(reparer, at=Point(2.36, 48.85, srid=4326), nom="Atelier test")

        page = solutions(
            client,
            geste="reparer",
            fiche="inconnue",
            longitude="2.36",
            latitude="48.85",
        )

        assert accessible_list(page) == ["Atelier test"]

    def test_the_accessible_list_says_when_there_is_no_place(self, client):
        page = solutions(client, geste="reparer", longitude="2.36", latitude="48.85")

        assert accessible_list(page) == ["Aucun lieu à proximité pour ce geste."]

    def test_the_map_message_is_a_live_region_from_the_start(self, client):
        """Screen readers only announce changes to a region already present."""
        page = solutions(client, geste="reparer")

        message = carte(page).select_one('[data-assistant-carte-target="message"]')
        assert message["role"] == "status"
        assert message["aria-live"] == "polite"
        assert message.has_attr("hidden")

    def test_the_synonyme_follows_back_to_the_fiche(self, client, fiche):
        page = solutions(client, geste="reparer", fiche=fiche.slug, synonyme="chaise")

        assert query_of(back_link(page)["href"])["synonyme"] == ["chaise"]

    def test_the_map_canvas_is_a_permanent_element_inside_the_map(self, client):
        """Turbo carries the canvas from screen to screen; here it lives in
        the map component, not parked at the end of the body."""
        page = solutions(client, geste="reparer")

        assert len(page.select("#assistant-carte-canvas")) == 1
        assert len(page.select("[data-turbo-permanent]")) == 1
        assert carte(page).select_one(
            "#assistant-carte-canvas.qfa-carte__canvas[data-turbo-permanent]"
        )

    def test_the_map_carries_the_first_geste_for_its_colour(self, client):
        page = solutions(client, geste=["reparer", "trier"])

        assert carte(page)["data-geste"] == "reparer"
