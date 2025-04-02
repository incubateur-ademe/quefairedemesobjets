# import pytest
from django.http import HttpRequest
from django.test import override_settings

from core.templatetags.seo_tags import get_sharer_content


class DummyObject:
    libelle = "Coucou"


class TestSharer:
    @override_settings(
        ASSISTANT={"HOSTS": ["quefairedemesdechets.domain"]},
        ALLOWED_HOSTS=["quefairedemesdechets.domain", "lvao.domain"],
    )
    def test_sharer_assistant(self):
        request = HttpRequest()
        request.GET = {}
        request.META["HTTP_HOST"] = "quefairedemesdechets.domain"
        sharer = get_sharer_content(request, DummyObject())
        assert "Coucou" not in sharer["email"]["url"]
        assert "lvao.domain" not in sharer["email"]["url"]
        assert "quefairedemesdechets.domain" in sharer["email"]["url"]

    @override_settings(
        ASSISTANT={"HOSTS": ["quefairedemesdechets.domain"]},
        ALLOWED_HOSTS=["quefairedemesdechets.domain", "lvao.domain"],
    )
    def test_sharer_carte(self):
        request = HttpRequest()
        request.GET = {}
        request.META["HTTP_HOST"] = "lvao.domain"
        sharer = get_sharer_content(request, DummyObject())

        assert "Coucou" in sharer["email"]["url"]
        assert "lvao.domain" in sharer["email"]["url"]
        assert "quefairedemesdechets.domain" not in sharer["email"]["url"]

    @override_settings(
        ASSISTANT={"HOSTS": ["quefairedemesdechets.domain"]},
        ALLOWED_HOSTS=["quefairedemesdechets.domain", "lvao.domain"],
    )
    def test_sharer_url(self):
        request = HttpRequest()
        request.GET = {}
        request.META["HTTP_HOST"] = "lvao.domain"
        sharer = get_sharer_content(request, DummyObject())
        assert sharer["url"].endswith("lvao.domain")
