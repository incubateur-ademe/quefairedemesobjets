import pytest
from django.urls import reverse

from assistant.parcours import Parcours
from unit_tests.assistant.helpers import (
    error_of,
    field,
    html_of,
    query_of,
    rename_search_term,
)
from unit_tests.qfdmd.qfdmod_factory import ProduitPageFactory

pytestmark = pytest.mark.django_db


class TestParcours:
    def test_reads_a_complete_input(self):
        parcours = Parcours.from_query(
            {
                "fiche": "meubles",
                "objet": "chaise",
                "adresse": "8 Rue de Rivoli 75004 Paris",
                "longitude": "2.35",
                "latitude": "48.85",
                "precise": "true",
            }
        )

        assert parcours.is_located
        assert parcours.precise
        assert parcours.longitude == 2.35
        assert parcours.fiche == "meubles"

    def test_unreadable_coordinate_counts_as_absent(self):
        """The user typed an address without choosing a suggestion."""
        parcours = Parcours.from_query({"adresse": "Paris", "longitude": "abc"})

        assert not parcours.is_located
        assert parcours.adresse == "Paris"

    def test_a_municipality_is_not_precise(self):
        parcours = Parcours.from_query({"adresse": "Lyon", "precise": ""})

        assert not parcours.precise

    def test_empty_values_are_not_carried(self):
        parcours = Parcours.from_query({"objet": "chaise"})

        assert parcours.as_params() == {"objet": "chaise"}

    def test_a_zero_coordinate_is_a_position(self):
        """The Greenwich meridian crosses Normandy: 0.0 is not "absent"."""
        parcours = Parcours(adresse="Villers-sur-Mer", longitude=0.0, latitude=49.32)

        assert Parcours.from_query(parcours.as_params()).is_located

    @pytest.mark.parametrize("value", ["nan", "inf", "-infinity"])
    def test_a_non_finite_coordinate_counts_as_absent(self, value):
        """`float("nan")` parses; sent to MapLibre it would break the map."""
        parcours = Parcours.from_query({"longitude": value, "latitude": "48.8"})

        assert not parcours.is_located

    def test_round_trip_through_params(self):
        departure = Parcours(
            fiche="meubles",
            objet="chaise",
            adresse="Auray",
            longitude=-2.98,
            latitude=47.66,
            precise=False,
        )

        arrival = Parcours.from_query(departure.as_params())

        assert arrival == departure


# An address as the autocomplete sends it: chosen, hence located.
AURAY = {"adresse": "Auray", "longitude": "-2.98", "latitude": "47.67"}


def search(client, **params):
    return client.get(reverse("assistant:recherche"), params)


def fiche_url(fiche):
    return reverse("assistant:produit", kwargs={"slug": fiche.slug})


class TestSearchView:
    def test_complete_input_leads_to_the_fiche(self, client, fiche):
        response = search(client, fiche=fiche.slug, objet=fiche.title, **AURAY)

        assert response.status_code == 302
        assert response.url.startswith(fiche_url(fiche))

    def test_the_address_is_optional(self, client, fiche):
        """Without an address, the fiche offers geolocation."""
        response = search(client, fiche=fiche.slug, objet=fiche.title)

        assert response.status_code == 302
        assert response.url.startswith(fiche_url(fiche))
        assert "adresse" not in query_of(response.url)

    def test_a_malformed_coordinate_does_not_block_the_search(self, client, fiche):
        """The address is optional: a bad coordinate must not send the user
        back home with an error no field shows."""
        response = search(client, fiche=fiche.slug, objet=fiche.title, longitude="abc")

        assert response.status_code == 302

    def test_an_address_typed_without_a_suggestion_is_refused(self, client, fiche):
        """Text the BAN did not resolve would be silently ignored by the map."""
        response = search(
            client, fiche=fiche.slug, objet=fiche.title, adresse="zzz nulle part"
        )

        assert response.status_code == 200
        assert error_of(html_of(response), "adresse").startswith(
            "Nous ne connaissons pas cette adresse"
        )

    def test_the_parcours_follows_to_the_fiche(self, client, fiche):
        response = search(client, fiche=fiche.slug, objet=fiche.title, **AURAY)

        query = query_of(response.url)
        assert query["longitude"] == ["-2.98"]
        assert query["adresse"] == ["Auray"]
        # The path carries the slug: the query string does not repeat it.
        assert "fiche" not in query

    @pytest.mark.parametrize("adresse", [{}, AURAY], ids=["no-address", "address"])
    def test_an_unknown_objet_shows_the_home_page_again(self, client, adresse):
        """The home page is rendered again with its messages rather than
        redirected to: a redirect would lose them."""
        response = search(client, objet="zzz inexistant", **adresse)

        assert response.status_code == 200
        page = html_of(response)
        assert error_of(page, "objet")
        assert field(page, "objet")["aria-invalid"] == "true"

    def test_a_missing_objet_shows_its_own_message(self, client):
        """Not "unknown objet": nothing was typed."""
        page = html_of(search(client, objet="", **AURAY))

        assert error_of(page, "objet") == (
            "Veuillez d'abord saisir un objet ou un déchet"
        )

    def test_the_input_is_kept_when_refused(self, client):
        page = html_of(search(client, objet="zzz inexistant", **AURAY))

        assert field(page, "objet")["value"] == "zzz inexistant"
        assert field(page, "adresse")["value"] == "Auray"


class TestSearchByLabel:
    """A shared URL only carries the label, never the slug."""

    def test_a_shared_url_opens_the_fiche(self, client, fiche):
        """The label is a search term, not a fiche title: "Téléphone mobile"
        leads to "Téléphones, tablettes ou consoles"."""
        rename_search_term(fiche, "Bidule test")

        response = search(client, objet="Bidule test", **AURAY)

        assert response.status_code == 302
        assert response.url.startswith(fiche_url(fiche))

    def test_a_draft_fiche_is_not_a_destination(self, client):
        """Every other lookup goes through `live()`: a shared label must not
        route to a page that then 404s."""
        draft = ProduitPageFactory(parent=None, live=False)
        rename_search_term(draft, "Brouillon test")

        response = search(client, objet="Brouillon test", **AURAY)

        assert response.status_code == 200
        assert error_of(html_of(response), "objet")

    def test_the_explicit_fiche_wins_over_the_label(self, client, fiche):
        """The autocomplete already decided: do not resolve again."""
        response = search(client, objet="peu importe", fiche=fiche.slug, **AURAY)

        assert response.url.startswith(fiche_url(fiche))


class TestHome:
    def test_only_the_objet_is_required(self, client):
        page = html_of(client.get(reverse("assistant:home")))

        assert field(page, "objet").has_attr("required")
        assert not field(page, "adresse").has_attr("required")

    def test_the_form_leaves_validation_to_the_server(self, client):
        """The browser tooltip would hide the designed message."""
        page = html_of(client.get(reverse("assistant:home")))

        form = page.select_one(f'form[action="{reverse("assistant:recherche")}"]')
        assert form.has_attr("novalidate")

    def test_the_coordinates_are_rendered_unlocalized(self, client):
        """French formatting writes "-1,55", which does not parse back: the
        position would be lost each time the field is shown again."""
        page = html_of(
            client.get(
                reverse("assistant:home"),
                {"longitude": "-1.555335", "latitude": "47.2"},
            )
        )

        assert page.select_one('input[name="longitude"]')["value"] == "-1.555335"
        assert page.select_one('input[name="latitude"]')["value"] == "47.2"

    def test_the_hidden_address_fields_are_present(self, client):
        """Without them, the map has no position to show."""
        page = html_of(client.get(reverse("assistant:home")))

        for name in ("longitude", "latitude", "precise"):
            assert page.select_one(f'input[type="hidden"][name="{name}"]'), name
