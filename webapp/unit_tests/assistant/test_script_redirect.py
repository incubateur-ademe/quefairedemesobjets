"""`iframe.js` is unchanged: it still opens the legacy `/dechet` routes. The
switch to the assistant V2 happens server side, per embedding host."""

import base64

import pytest
from django.test import RequestFactory

from qfdmd.middleware import RequestEnhancementMiddleware
from unit_tests.qfdmd.qfdmod_factory import ProduitPageFactory

BETA = {"V2_HOSTS": ["beta.example.fr"], "V2_BASE_URL": ""}


def ref(url):
    return base64.b64encode(url.encode()).decode()


def redirect_for(path, params):
    """The legacy home needs a Wagtail homepage to render: ask the middleware
    directly whether it would leave the request alone."""
    request = RequestFactory().get(path, params)
    return RequestEnhancementMiddleware(None)._redirect_beta_hosts_to_assistant_v2(
        request
    )


@pytest.mark.django_db
class TestScriptRedirect:
    @pytest.fixture(autouse=True)
    def beta(self, settings):
        settings.ASSISTANT = BETA
        settings.BASE_URL = "https://qfdmo.fr"

    def test_whitelisted_host_opens_assistant_v2(self, client):
        response = client.get(
            "/", {"s": "1", "ref": ref("https://beta.example.fr/p?x=1")}
        )
        assert response.status_code == 302
        assert response.url.startswith("https://qfdmo.fr/assistant/?")
        assert "s=1" in response.url and "ref=" in response.url
        assert response.headers["Cache-Control"].startswith("max-age=0, no-cache")

    def test_assistant_v2_can_live_on_its_own_domain(self, client, settings):
        settings.ASSISTANT = {**BETA, "V2_BASE_URL": "https://betatest.qfdmo.fr/"}
        response = client.get("/", {"ref": ref("https://beta.example.fr/")})
        assert response.url.startswith("https://betatest.qfdmo.fr/assistant/?")

    def test_the_script_route_reaches_assistant_v2(self, client):
        """`iframe.js` opens `/dechet`, which the legacy app already sends home."""
        response = client.get(
            "/dechet", {"s": "1", "ref": ref("https://beta.example.fr/")}
        )
        assert response.status_code == 301
        response = client.get(response.url)
        assert response.status_code == 302
        assert response.url.startswith("https://qfdmo.fr/assistant/?")

    def test_data_objet_preselects_the_fiche(self, client):
        page = ProduitPageFactory(parent=None)
        response = client.get(
            f"/dechet/{page.slug}/", {"ref": ref("https://beta.example.fr/")}
        )
        assert response.status_code == 302
        assert response.url.startswith(
            f"https://qfdmo.fr/assistant/objet/{page.slug}/?"
        )

    def test_unknown_fiche_stays_on_legacy(self):
        assert (
            redirect_for("/dechet/inconnu/", {"ref": ref("https://beta.example.fr/")})
            is None
        )

    def test_other_host_stays_on_legacy(self):
        assert redirect_for("/", {"ref": ref("https://autre.example.fr/")}) is None

    @pytest.mark.parametrize("bad_ref", ["", "%%%", "pas-du-base64", ref("\xff")])
    def test_unreadable_ref_stays_on_legacy(self, bad_ref):
        assert redirect_for("/", {"ref": bad_ref}) is None

    def test_without_the_script_nothing_changes(self):
        assert redirect_for("/", {}) is None

    def test_other_routes_are_never_redirected(self):
        assert redirect_for("/carte", {"ref": ref("https://beta.example.fr/")}) is None
