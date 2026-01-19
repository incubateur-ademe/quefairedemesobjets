import pytest
from bs4 import BeautifulSoup
from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import override_settings

from qfdmd.models import Suggestion, Synonyme
from unit_tests.qfdmd.qfdmod_factory import (
    ProduitFactory,
    SuggestionFactory,
    SynonymeFactory,
)


@pytest.fixture
def get_response(client):
    @override_settings(
        ASSISTANT={**settings.ASSISTANT, "HOSTS": ["coucou.youpi"]},
        ALLOWED_HOSTS=["coucou.youpi"],
    )
    def _get_response(path=""):
        url = f"/{path}"
        response = client.get(url, headers={"host": "coucou.youpi"})
        assert response.status_code == 200, "No redirect occurs"
        return response, BeautifulSoup(response.content, "html.parser")

    return _get_response


@pytest.mark.django_db
class TestHomepage:
    def test_patchwork(self, get_response, tmp_path):
        p = tmp_path / "picto.svg"
        picto = SimpleUploadedFile(p, b"<svg>coucou</svg>")
        produit = ProduitFactory()
        SynonymeFactory(picto=picto, pin_on_homepage=True, produit=produit)
        _, soup = get_response()

        assert (
            len(soup.css.select("[data-testid=patchwork-icon]"))
            == Synonyme.objects.filter(pin_on_homepage=True)
            .exclude(picto="")
            .exclude(picto=None)
            .count()
        )
        assert soup.css.select("[data-testid=patchwork-icon]")[0]

    def test_none_in_modal(self, get_response):
        response, soup = get_response()
        modal = soup.find(id="fr-modal-partager-le-site")
        assert "None" not in modal.get_text()

    def test_suggestions(self, get_response, tmp_path):
        produit = ProduitFactory(nom="Coucou le produit")
        synonyme = SynonymeFactory(produit=produit, nom="Youpi le synonyme")
        SuggestionFactory(produit=synonyme)
        response, soup = get_response()
        assert (
            len(soup.css.select("[data-testid=suggestion]"))
            == Suggestion.objects.all().count()
        )
        assert (
            soup.css.select("[data-testid=suggestion]")[0].text.lower().strip()
            == "Youpi le synonyme".lower()
        )
