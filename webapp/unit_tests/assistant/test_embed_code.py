"""The embed code names the synonyme the visitor searched for. `data-objet`
keeps the fiche, so a synonyme removed later never breaks an embed."""

import pytest
from django.test import RequestFactory

from core.templatetags.script_tags import (
    generate_iframe_script,
    page_formatted_for_script,
)
from qfdmd.models import ProduitPageSearchTerm, SearchTag, TaggedSearchTag
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


def test_through_a_synonyme_the_code_names_it(fiche):
    tag = tag_of(fiche)
    request = searched(tag)

    script = generate_iframe_script(request, page=fiche)

    assert f'data-objet="{fiche.slug}"' in script
    assert 'data-synonyme="mixeur"' in script
    assert page_formatted_for_script({"page": fiche, "request": request}) == (
        "Page “Mixeur - Petit électroménager”"
    )


def test_without_a_search_nothing_changes(fiche):
    script = generate_iframe_script(searched(), page=fiche)

    assert f'data-objet="{fiche.slug}"' in script
    assert "data-synonyme" not in script
    assert page_formatted_for_script({"page": fiche, "request": searched()}) == (
        "Page “Petit électroménager”"
    )


def test_the_fiche_title_is_not_a_synonyme(fiche):
    term = ProduitPageSearchTerm.objects.get(produit_page=fiche)

    assert "data-synonyme" not in generate_iframe_script(searched(term), page=fiche)


def test_a_synonyme_of_another_fiche_is_left_out(fiche):
    other = tag_of(ProduitPageFactory(parent=None))

    assert "data-synonyme" not in generate_iframe_script(searched(other), page=fiche)


def test_an_unknown_search_term_is_left_out(fiche):
    request = RequestFactory().get("/")
    request.COOKIES["qf_search_term_id"] = "0"

    assert "data-synonyme" not in generate_iframe_script(request, page=fiche)
