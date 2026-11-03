import pytest
from django.urls import reverse

from assistant.urls import urlpatterns
from unit_tests.assistant.helpers import html_of
from unit_tests.qfdmo.acteur_factory import DisplayedActeurFactory

pytestmark = pytest.mark.django_db

FRAGMENT = {"Turbo-Frame": "assistant-fiche"}


class TestRoutes:
    def test_every_screen_url_ends_with_a_slash(self):
        """One shape for the screens: Django's APPEND_SLASH then never redirects."""
        screens = {"home", "recherche", "produit", "solutions", "lieu"}
        for pattern in urlpatterns:
            route = str(pattern.pattern)
            if pattern.name in screens:
                assert route == "" or route.endswith("/"), route

    def test_home_responds(self, client):
        assert client.get(reverse("assistant:home")).status_code == 200

    def test_solutions_responds(self, client):
        assert client.get(reverse("assistant:solutions")).status_code == 200

    def test_produit_responds(self, client, fiche):
        response = client.get(reverse("assistant:produit", args=[fiche.slug]))

        assert response.status_code == 200

    def test_lieu_responds(self, client):
        acteur = DisplayedActeurFactory()

        response = client.get(reverse("assistant:lieu", args=[acteur.uuid]))

        assert response.status_code == 200

    def test_unknown_produit_returns_404(self, client):
        response = client.get(reverse("assistant:produit", args=["inconnu"]))

        assert response.status_code == 404


class TestLayout:
    def test_serves_full_document_without_turbo_header(self, client):
        response = client.get(reverse("assistant:home"))

        assert b"<!DOCTYPE html>" in response.content

    def test_serves_fragment_with_turbo_header(self, client):
        """Turbo only extracts the frame: rendering the layout would be wasted work."""
        response = client.get(reverse("assistant:home"), headers=FRAGMENT)

        assert b"<!DOCTYPE html>" not in response.content

    def test_layout_carries_no_dsfr(self, client):
        """The assistant has its own design system."""
        content = client.get(reverse("assistant:home")).content.decode()

        assert "dsfr" not in content.lower()

    def test_layout_has_skiplink(self, client):
        """RGAA 12.7: without {% dsfr_skiplinks %}, ours must be there."""
        page = html_of(client.get(reverse("assistant:home")))

        assert page.select_one('a.qfa-skiplink[href="#contenu"]')
        assert page.select_one("main#contenu")

    def test_layout_forbids_snapshot_previews(self, client):
        """Turbo animates once per visit: with a cached preview, the real page
        then lands without transition and the map controller connects twice."""
        page = html_of(client.get(reverse("assistant:home")))

        meta = page.select_one('meta[name="turbo-cache-control"]')
        assert meta["content"] == "no-preview"

    def test_layout_is_not_indexed(self, client):
        """No SEO for content embedded in an iframe."""
        page = html_of(client.get(reverse("assistant:home")))

        assert "noindex" in page.select_one('meta[name="robots"]')["content"]

    def test_layout_parks_the_map_canvas_and_enables_view_transitions(self, client):
        """Off the solutions screen, the permanent canvas waits at the end of
        the body; Turbo Drive animates screen changes."""
        page = html_of(client.get(reverse("assistant:home")))

        canvas = page.select_one("#assistant-carte-canvas")
        assert canvas.has_attr("data-turbo-permanent")
        assert canvas.parent.name == "body"
        meta = page.select_one('meta[name="view-transition"]')
        assert meta["content"] == "same-origin"

    def test_a_fragment_does_not_park_the_canvas(self, client):
        page = html_of(client.get(reverse("assistant:home"), headers=FRAGMENT))

        assert page.select_one("#assistant-carte-canvas") is None
