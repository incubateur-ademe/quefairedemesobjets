from unittest.mock import patch

import pytest
from bs4 import BeautifulSoup
from django.urls import reverse
from wagtail.models import Page

from unit_tests.qfdmd.qfdmod_factory import PageFactory


def home_page(client):
    """Served with the quefaire.html layout"""
    page = PageFactory(parent=Page.objects.get(depth=1), title="Accueil")
    with patch("qfdmd.views.get_homepage", return_value=page):
        return client.get("/")


def infotri_page(client):
    """Served with the base.html layout"""
    return client.get(reverse("infotri:configurator"))


def robots_meta(response):
    assert response.status_code == 200
    soup = BeautifulSoup(response.content, "html.parser")
    return [meta["content"] for meta in soup.select('meta[name="robots"]')]


# Previews have no nginx to send X-Robots-Tag: BLOCK_ROBOTS is their noindex.
@pytest.mark.django_db
@pytest.mark.parametrize("page", [home_page, infotri_page])
class TestBlockRobots:
    def test_block_robots_adds_noindex(self, client, settings, page):
        settings.BLOCK_ROBOTS = True
        assert "noindex, nofollow" in robots_meta(page(client))

    def test_pages_are_indexed_by_default(self, client, settings, page):
        settings.BLOCK_ROBOTS = False
        assert not [c for c in robots_meta(page(client)) if "noindex" in c]
