import json

import pytest
from django.contrib.auth.models import AnonymousUser
from django.template.loader import render_to_string
from django.test import RequestFactory

from core.context_processors import global_context
from core.templatetags.carte_tags import maplibre_locale
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


@pytest.mark.django_db
def test_carte_view_mode_nav_label_comes_from_settings():
    AccessibilitySettings.objects.create(view_mode_nav_label="Choisir l'affichage")
    request = RequestFactory().get("/")
    request.user = AnonymousUser()

    html = render_to_string(
        "ui/components/carte/header.html",
        {"forms": {"view_mode": ""}, "mode_liste": False},
        request=request,
    )

    assert 'aria-label="Choisir l&#x27;affichage"' in html


@pytest.mark.django_db
def test_maplibre_locale_comes_from_settings():
    AccessibilitySettings.objects.create(
        map_title="Plan", map_zoom_in="Agrandir", map_popup_close="Fermer"
    )
    request = RequestFactory().get("/")

    locale = json.loads(maplibre_locale({"request": request}))

    assert locale["Map.Title"] == "Plan"
    assert locale["NavigationControl.ZoomIn"] == "Agrandir"
    assert locale["Popup.Close"] == "Fermer"
    assert locale["NavigationControl.ZoomOut"] == "Dézoomer"


@pytest.mark.django_db
def test_carte_fiche_labels_come_from_settings():
    from core.templatetags.share_tags import get_sharer_content

    AccessibilitySettings.objects.create(
        acteur_close_label="Quitter la fiche",
        acteur_tabs_label="Onglets du lieu",
        share_label="diffuser",
        new_window_mention="onglet neuf",
        list_region_label="Résultats en liste",
    )
    request = RequestFactory().get("/")

    assert 'aria-label="Résultats en liste"' in render_to_string(
        "ui/components/carte/mode_liste.html", request=request
    )
    assert ">diffuser<" in render_to_string(
        "ui/components/acteur/_action_share.html", request=request
    )
    assert 'aria-label="Onglets du lieu ' in render_to_string(
        "ui/components/acteur/_tabs.html", {"adresse": "1 rue X"}, request=request
    )
    assert "Quitter la fiche" in render_to_string(
        "ui/components/acteur/acteur_detail.html",
        {"adresse": "1 rue X"},
        request=request,
    )

    request.resolver_match = type("M", (), {"view_name": "qfdmd:home"})()
    title = get_sharer_content(request, "Lieu", "facebook")["title"]
    assert title == "diffuser Lieu sur Facebook - onglet neuf"
