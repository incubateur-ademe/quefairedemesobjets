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


@pytest.mark.django_db
def test_templates_read_labels_from_settings_with_or_without_request():
    from django.template.loader import render_to_string

    AccessibilitySettings.objects.create(
        loading_label="Patientez", map_region_label="Plan des lieux"
    )

    assert "Patientez" in render_to_string("ui/components/spinner.html")
    assert 'aria-label="Plan des lieux"' in render_to_string(
        "ui/components/carte/mode_carte.html", request=RequestFactory().get("/")
    )
