import pytest
from django.urls import reverse

from assistant.parcours import Parcours
from qfdmd.models import ProduitPageSearchTerm

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


@pytest.fixture
def fiche():
    """A live fiche: `ModelChoiceField` checks that it really exists."""
    from unit_tests.qfdmd.qfdmod_factory import ProduitPageFactory

    return ProduitPageFactory(parent=None)


class TestSearchView:
    def test_complete_input_leads_to_the_fiche(self, client, fiche):
        response = client.get(
            reverse("assistant:recherche"),
            {"fiche": fiche.slug, "objet": fiche.title, "adresse": "Auray"},
        )

        assert response.status_code == 302
        assert response.url.startswith(
            reverse("assistant:produit", kwargs={"slug": fiche.slug})
        )

    def test_the_parcours_follows_to_the_fiche(self, client, fiche):
        response = client.get(
            reverse("assistant:recherche"),
            {
                "fiche": fiche.slug,
                "objet": fiche.title,
                "adresse": "Auray",
                "longitude": "-2.98",
                "latitude": "47.66",
            },
        )

        assert "longitude=-2.98" in response.url
        assert "adresse=Auray" in response.url
        # The path carries the slug: the query string does not repeat it.
        assert "fiche=" not in response.url

    @pytest.mark.parametrize(
        "params",
        [
            {"objet": "zzz inconnu", "adresse": "Auray"},  # unresolved objet
            {"objet": "Emballages"},  # no address
        ],
    )
    def test_incomplete_input_shows_the_home_page_again(self, client, params):
        """Both fields are required (#3295). The home page is rendered again
        with its messages rather than redirected to: a redirect would lose them."""
        response = client.get(reverse("assistant:recherche"), params)

        assert response.status_code == 200
        assert "qfa-combobox__erreur" in response.content.decode()


class TestHome:
    def test_both_fields_are_required(self, client):
        content = client.get(reverse("assistant:home")).content.decode()

        assert content.count("required") >= 2

    def test_the_hidden_address_fields_are_present(self, client):
        """Without them, the map has no position to show."""
        content = client.get(reverse("assistant:home")).content.decode()

        for name in ("longitude", "latitude", "precise"):
            assert f'name="{name}"' in content


class TestSearchForm:
    """A shared URL only carries the label, never the slug."""

    def test_a_shared_url_opens_the_fiche(self, client):
        """ "?objet=<label>" must lead to the fiche, not to a frozen form.

        The label is a search term, not a fiche title: "Téléphone mobile"
        leads to "Téléphones, tablettes ou consoles".
        """
        from unit_tests.qfdmd.qfdmod_factory import ProduitPageFactory

        fiche = ProduitPageFactory(parent=None)
        # The factory already creates the fiche's search term (one-to-one
        # relation): rename it rather than add a second one.
        term = ProduitPageSearchTerm.objects.get(produit_page=fiche)
        term.searchable_title = "Bidule test"
        term.save()

        response = client.get(
            reverse("assistant:recherche"), {"objet": "Bidule test", "adresse": "Auray"}
        )

        assert response.status_code == 302
        assert response.url.startswith(
            reverse("assistant:produit", kwargs={"slug": fiche.slug})
        )

    def test_the_explicit_fiche_wins_over_the_label(self, client, fiche):
        """The autocomplete already decided: do not resolve again."""
        response = client.get(
            reverse("assistant:recherche"),
            {"objet": "peu importe", "fiche": fiche.slug, "adresse": "Auray"},
        )

        assert response.url.startswith(
            reverse("assistant:produit", kwargs={"slug": fiche.slug})
        )

    def test_an_unknown_objet_shows_an_error(self, client):
        """A silent redirect left the user in front of a filled form that
        refused to move on, without saying why."""
        response = client.get(
            reverse("assistant:recherche"),
            {"objet": "zzz inexistant", "adresse": "Auray"},
        )

        assert response.status_code == 200
        content = response.content.decode()
        assert "qfa-combobox__erreur" in content
        assert 'aria-invalid="true"' in content

    def test_a_missing_address_shows_an_error(self, client, fiche):
        response = client.get(reverse("assistant:recherche"), {"fiche": fiche.slug})

        assert response.status_code == 200
        assert "qfa-combobox__erreur" in response.content.decode()

    def test_the_input_is_kept_when_refused(self, client):
        content = client.get(
            reverse("assistant:recherche"),
            {"objet": "zzz inexistant", "adresse": "Auray"},
        ).content.decode()

        assert 'value="zzz inexistant"' in content
        assert 'value="Auray"' in content
