import pytest
from django.template.loader import render_to_string
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


@pytest.mark.django_db
def test_new_window_mention_comes_from_settings():
    AccessibilitySettings.objects.create(new_window_mention="nouvel onglet")

    html = render_to_string(
        "ui/components/lien/lien.html",
        {"lien": {"url": "https://a.fr", "titre_du_lien": "Un lien"}},
        request=RequestFactory().get("/"),
    )

    assert 'title="Un lien - nouvel onglet"' in html


@pytest.mark.django_db
def test_footer_and_modal_labels_come_from_settings():
    from django.template.loader import render_to_string

    AccessibilitySettings.objects.create(
        modal_close_label="Refermer la boite", footer_nav_label="Liens utiles"
    )

    assert 'title="Refermer la boite"' in render_to_string(
        "ui/components/modals/base.html",
        {"id": "x"},
        request=RequestFactory().get("/"),
    )
    assert 'aria-label="Liens utiles"' in render_to_string(
        "ui/components/footer/base.html", request=RequestFactory().get("/")
    )


@pytest.mark.django_db
def test_produit_state_tabs_label_comes_from_settings():
    from django.template.loader import render_to_string

    AccessibilitySettings.objects.create(produit_state_tabs_label="Etat de")

    class Produit:
        qu_est_ce_que_j_en_fais = ""
        sous_categorie_with_carte_display = False

        def __str__(self):
            return "Velo"

    html = render_to_string(
        "ui/components/produit/produit.html",
        {"bon_etat": "a", "mauvais_etat": "b", "produit": Produit()},
    )
    assert 'aria-label="Etat de Velo"' in html
