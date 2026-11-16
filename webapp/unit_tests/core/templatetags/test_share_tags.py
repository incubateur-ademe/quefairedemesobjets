import pytest
from django.test import RequestFactory
from django.urls import resolve

from core.templatetags.share_tags import get_sharer_content
from qfdmd.models import AccessibilitySettings


@pytest.mark.django_db
def test_share_titles_use_the_new_window_mention_setting():
    AccessibilitySettings.objects.create(new_window_mention="nouvel onglet")
    request = RequestFactory().get("/")
    request.resolver_match = resolve("/")

    sharer = get_sharer_content(request, "Un objet")

    assert (
        sharer["facebook"]["title"] == "partager Un objet sur Facebook - nouvel onglet"
    )
