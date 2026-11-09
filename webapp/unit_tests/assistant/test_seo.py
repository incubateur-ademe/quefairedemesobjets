"""The assistant lives in iframes only and stays out of search engines."""

import pytest
from django.urls import reverse
from wagtail.models import Site

from unit_tests.qfdmd.qfdmod_factory import ProduitPageFactory

pytestmark = pytest.mark.django_db

STANDALONE = {"Sec-Fetch-Dest": "document"}


@pytest.fixture
def standalone_redirect(settings):
    settings.ASSISTANT = {**settings.ASSISTANT, "V2_STANDALONE_REDIRECT": True}


@pytest.fixture
def fiche_on_the_site():
    """A fiche with a URL on the site: under the root page of the default site."""
    return ProduitPageFactory(parent=Site.objects.get(is_default_site=True).root_page)


class TestNoindex:
    def test_tells_search_engines_not_to_index_a_screen(self, client):
        response = client.get(reverse("assistant:home"))

        assert response["X-Robots-Tag"] == "noindex, nofollow"

    def test_leaves_the_rest_of_the_site_alone(self, client):
        assert "X-Robots-Tag" not in client.get("/robots.txt")


class TestOutsideAnIframe:
    def test_a_fiche_redirects_to_its_page_on_the_site(
        self, client, standalone_redirect, fiche_on_the_site
    ):
        url = reverse("assistant:produit", args=[fiche_on_the_site.slug])

        response = client.get(url, headers=STANDALONE)

        assert (response.status_code, response.url) == (301, fiche_on_the_site.url)

    def test_solutions_redirect_to_the_fiche_they_carry(
        self, client, standalone_redirect, fiche_on_the_site
    ):
        response = client.get(
            reverse("assistant:solutions"),
            {"geste": "reparer", "fiche": fiche_on_the_site.slug},
            headers=STANDALONE,
        )

        assert response.url == fiche_on_the_site.url

    def test_a_screen_without_fiche_redirects_to_the_home_page(
        self, client, standalone_redirect
    ):
        response = client.get(reverse("assistant:home"), headers=STANDALONE)

        assert (response.status_code, response.url) == (301, reverse("qfdmd:home"))

    def test_the_redirect_is_noindex_and_varies_with_the_destination(
        self, client, standalone_redirect
    ):
        response = client.get(reverse("assistant:home"), headers=STANDALONE)

        assert response["X-Robots-Tag"] == "noindex, nofollow"
        assert "Sec-Fetch-Dest" in response["Vary"]

    @pytest.mark.parametrize(
        "headers",
        [{"Sec-Fetch-Dest": "iframe"}, {"Sec-Fetch-Dest": "empty"}, {}],
        ids=["iframe", "turbo", "no header"],
    )
    def test_serves_the_iframe_its_navigations_and_bots(
        self, client, standalone_redirect, headers
    ):
        assert client.get(reverse("assistant:home"), headers=headers).status_code == 200

    def test_serves_every_request_when_turned_off(self, client, settings):
        settings.ASSISTANT = {**settings.ASSISTANT, "V2_STANDALONE_REDIRECT": False}

        response = client.get(reverse("assistant:home"), headers=STANDALONE)

        assert response.status_code == 200
