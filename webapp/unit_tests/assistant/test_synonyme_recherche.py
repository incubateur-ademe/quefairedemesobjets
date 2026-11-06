"""The synonyme picked in the V2 suggestions or given by an embed travels by
its slug. `data-objet` keeps the fiche: an unknown synonyme is ignored,
never a 404."""

import pytest
from django.test import RequestFactory
from django.urls import reverse

from assistant.objets import _suggestion, synonyme_label
from assistant.parcours import Parcours
from core.templatetags.script_tags import (
    generate_iframe_script,
    page_formatted_for_script,
)
from qfdmd.models import ProduitPageSearchTerm, SearchTag, TaggedSearchTag
from unit_tests.assistant.helpers import query_of
from unit_tests.qfdmd.qfdmod_factory import ProduitPageFactory

pytestmark = pytest.mark.django_db


@pytest.fixture
def fiche():
    return ProduitPageFactory(parent=None, title="Petit électroménager")


def tag_of(page, name="mixeur"):
    tag = SearchTag.objects.create(name=name, slug=name)
    TaggedSearchTag.objects.create(tag=tag, content_object=page)
    return tag


def searched(term=None):
    request = RequestFactory().get("/")
    if term is not None:
        request.COOKIES["qf_search_term_id"] = str(term.pk)
    return request


class TestSuggestion:
    def test_a_synonyme_carries_its_slug(self, fiche):
        tag = tag_of(fiche)

        assert _suggestion(tag) == {
            "label": "Mixeur",
            "slug": fiche.slug,
            "synonyme": "mixeur",
        }

    def test_the_fiche_title_carries_no_synonyme(self, fiche):
        term = ProduitPageSearchTerm.objects.get(produit_page=fiche)

        assert "synonyme" not in _suggestion(term)


class TestSynonymeLabel:
    def test_label_of_a_synonyme_of_the_fiche(self, fiche):
        tag_of(fiche)

        assert synonyme_label("mixeur", fiche) == "Mixeur"

    def test_a_synonyme_of_another_fiche_is_ignored(self, fiche):
        tag_of(ProduitPageFactory(parent=None))

        assert synonyme_label("mixeur", fiche) == ""

    @pytest.mark.parametrize("value", ["", "inconnu"])
    def test_no_or_unknown_slug(self, fiche, value):
        assert synonyme_label(value, fiche) == ""


class TestParcours:
    def test_round_trip(self):
        assert Parcours.from_query({"synonyme": " mixeur "}).as_params() == {
            "synonyme": "mixeur"
        }


class TestProduitPage:
    def test_the_field_shows_the_synonyme(self, client, fiche):
        tag_of(fiche)

        response = client.get(
            reverse("assistant:produit", kwargs={"slug": fiche.slug}),
            {"synonyme": "mixeur"},
        )

        assert response.context["parcours"].objet == "Mixeur"
        assert "synonyme=mixeur" in response.context["parametres"]

    def test_an_unknown_synonyme_shows_the_fiche(self, client, fiche):
        response = client.get(
            reverse("assistant:produit", kwargs={"slug": fiche.slug}),
            {"synonyme": "supprime-depuis"},
        )

        assert response.status_code == 200
        assert response.context["parcours"].objet == fiche.title
        assert "synonyme" not in response.context["parametres"]

    def test_the_search_keeps_the_synonyme_to_the_fiche(self, client, fiche):
        tag_of(fiche)

        response = client.get(
            reverse("assistant:recherche"),
            {"fiche": fiche.slug, "objet": "Mixeur", "synonyme": "mixeur"},
        )

        assert query_of(response.url)["synonyme"] == ["mixeur"]


class TestEmbedCode:
    def test_through_a_synonyme_the_code_names_it(self, fiche):
        tag = tag_of(fiche)
        request = searched(tag)

        script = generate_iframe_script(request, page=fiche)

        assert f'data-objet="{fiche.slug}"' in script
        assert 'data-synonyme="mixeur"' in script
        assert page_formatted_for_script({"page": fiche, "request": request}) == (
            "Page “Mixeur - Petit électroménager”"
        )

    def test_without_a_synonyme_nothing_changes(self, fiche):
        script = generate_iframe_script(searched(), page=fiche)

        assert f'data-objet="{fiche.slug}"' in script
        assert "data-synonyme" not in script
        assert page_formatted_for_script({"page": fiche, "request": searched()}) == (
            "Page “Petit électroménager”"
        )

    def test_a_synonyme_of_another_fiche_is_left_out(self, fiche):
        other = tag_of(ProduitPageFactory(parent=None))

        assert "data-synonyme" not in generate_iframe_script(
            searched(other), page=fiche
        )
