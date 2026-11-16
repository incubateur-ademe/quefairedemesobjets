import pytest
from django.test import RequestFactory

from core.context_processors import global_context
from qfdmd.models import AccessibilitySettings


@pytest.mark.django_db
def test_accessibility_labels_come_from_settings():
    AccessibilitySettings.objects.create(
        header_search_label="Chercher dans le site",
        home_search_label="Chercher un objet",
        skiplink_content_label="Aller au contenu",
    )

    context = global_context(RequestFactory().get("/"))

    forms = context["assistant"]
    assert (
        forms["header_search_form"].fields["search"].widget.attrs["title"]
        == "Chercher dans le site"
    )
    assert (
        forms["homepage_search_form"].fields["search"].widget.attrs["title"]
        == "Chercher un objet"
    )
    assert context["skiplinks"][0]["label"] == "Aller au contenu"
