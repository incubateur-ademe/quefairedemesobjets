from django.http import HttpRequest

from core.templatetags.seo_tags import get_sharer_content


class DummyObject:
    libelle = "Coucou"


class TestSharer:
    # FIXME: simuler la route /carte
    def test_sharer_assistant(self):
        request = HttpRequest()
        request.GET = {}
        sharer = get_sharer_content(request, DummyObject())
        assert "Coucou" not in sharer["email"]["url"]
        assert "lvao.domain" not in sharer["email"]["url"]
        assert "quefairedemesdechets.domain" in sharer["email"]["url"]

    # FIXME: simuler la route /un-produit
    def test_sharer_carte(self):
        request = HttpRequest()
        request.GET = {}
        sharer = get_sharer_content(request, DummyObject())

        assert "Coucou" in sharer["email"]["url"]
        assert "lvao.domain" in sharer["email"]["url"]
        assert "quefairedemesdechets.domain" not in sharer["email"]["url"]

    # FIXME: rewrite test
    def test_sharer_url(self):
        request = HttpRequest()
        request.GET = {}
        sharer = get_sharer_content(request, DummyObject())
        assert sharer["url"].endswith("lvao.domain")
