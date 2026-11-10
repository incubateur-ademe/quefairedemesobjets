"""`iframe.js` is unchanged: it still opens the legacy `/dechet` routes. The
switch to the assistant V2 happens server side, for bare `<iframe>` embeds too."""

import base64

import pytest
from django.test import RequestFactory

from qfdmd.middleware import RequestEnhancementMiddleware
from qfdmd.models import LegacyIntermediateProduitPage
from unit_tests.assistant.helpers import query_of
from unit_tests.qfdmd.qfdmod_factory import SynonymeFactory


def ref(url):
    return base64.b64encode(url.encode()).decode()


def redirect_for(path, params, headers=None):
    """The legacy home needs a Wagtail homepage to render: ask the middleware
    directly whether it would leave the request alone."""
    request = RequestFactory().get(path, params, headers=headers)
    middleware = RequestEnhancementMiddleware(None)
    middleware._prepare_request_if_iframe(request)
    return middleware._redirect_embeds_to_assistant_v2(request)


@pytest.mark.django_db
class TestScriptRedirect:
    @pytest.fixture(autouse=True)
    def base_url(self, settings):
        settings.BASE_URL = "https://qfdmo.fr"

    def test_any_embedder_opens_assistant_v2(self, client):
        response = client.get(
            "/", {"s": "1", "ref": ref("https://reutilisateur.example.fr/p?x=1")}
        )
        assert response.status_code == 302
        assert response.url.startswith("https://qfdmo.fr/assistant/?")
        assert query_of(response.url)["s"] == ["1"]
        assert "ref" in query_of(response.url)
        assert response.headers["Cache-Control"].startswith("max-age=0, no-cache")

    def test_bare_iframe_opens_assistant_v2(self, client, fiche):
        """No `iframe.js`, so no `ref`: the browser still says it is an iframe."""
        response = client.get("/", {"s": "1"}, headers={"Sec-Fetch-Dest": "iframe"})
        assert response.status_code == 302
        assert response.url == "https://qfdmo.fr/assistant/?s=1"
        response = client.get(
            f"/dechet/{fiche.slug}/", headers={"Sec-Fetch-Dest": "iframe"}
        )
        assert response.url == f"https://qfdmo.fr/assistant/objet/{fiche.slug}/"

    def test_a_visit_to_the_site_stays_on_legacy(self):
        assert redirect_for("/", {}, headers={"Sec-Fetch-Dest": "document"}) is None

    def test_the_script_route_reaches_assistant_v2(self, client):
        """`iframe.js` opens `/dechet`, which the legacy app already sends home."""
        response = client.get(
            "/dechet", {"s": "1", "ref": ref("https://reutilisateur.example.fr/")}
        )
        assert response.status_code == 301
        response = client.get(response.url)
        assert response.status_code == 302
        assert response.url.startswith("https://qfdmo.fr/assistant/?")

    def test_data_objet_preselects_the_fiche(self, client, fiche):
        response = client.get(
            f"/dechet/{fiche.slug}/", {"ref": ref("https://reutilisateur.example.fr/")}
        )
        assert response.status_code == 302
        assert response.url.startswith(
            f"https://qfdmo.fr/assistant/objet/{fiche.slug}/?"
        )

    def test_data_synonyme_travels_to_the_fiche(self, client, fiche):
        """`iframe.js` forwards `data-synonyme` as is: the fiche shows it."""
        response = client.get(
            f"/dechet/{fiche.slug}/",
            {"synonyme": "mixeur", "ref": ref("https://reutilisateur.example.fr/")},
        )
        assert response.url.startswith(
            f"https://qfdmo.fr/assistant/objet/{fiche.slug}/?"
        )
        assert query_of(response.url)["synonyme"] == ["mixeur"]

    def test_legacy_synonyme_opens_its_fiche(self, client, fiche):
        """Embedders pass synonyme slugs (`montre-connectee`): follow them to
        their fiche, as the legacy assistant does."""
        synonyme = SynonymeFactory(nom="Montre connectée")
        LegacyIntermediateProduitPage.objects.create(
            page=fiche, produit=synonyme.produit
        )
        response = client.get(
            f"/dechet/{synonyme.slug}/",
            {"ref": ref("https://reutilisateur.example.fr/")},
        )
        assert response.status_code == 302
        assert response.url.startswith(
            f"https://qfdmo.fr/assistant/objet/{fiche.slug}/?"
        )

    def test_unknown_fiche_stays_on_legacy(self):
        assert (
            redirect_for(
                "/dechet/inconnu/", {"ref": ref("https://reutilisateur.example.fr/")}
            )
            is None
        )

    def test_without_the_script_nothing_changes(self):
        assert redirect_for("/", {}) is None

    def test_other_routes_are_never_redirected(self):
        assert (
            redirect_for("/carte", {"ref": ref("https://reutilisateur.example.fr/")})
            is None
        )
