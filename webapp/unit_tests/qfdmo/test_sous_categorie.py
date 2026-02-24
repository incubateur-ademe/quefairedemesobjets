import pytest

from qfdmo.models import SousCategorieObjet
from unit_tests.qfdmo.sscatobj_factory import SousCategorieObjetFactory


class TestSousCategorieObjetStr:
    def test_str_blank(self):
        assert SousCategorieObjetFactory.build(libelle="").__str__() == ""

    def test_str_specialchar(self):
        assert "Åctïôn" in SousCategorieObjetFactory.build(libelle="Åctïôn").__str__()


class TestActionNaturalKey:
    def test_natural_key(self):
        assert SousCategorieObjetFactory.build(
            libelle="Natural key", code="natural_key"
        ).natural_key() == ("natural_key",)

    @pytest.mark.django_db()
    def test_get_natural_key(self):
        some_sous_categorie = SousCategorieObjetFactory(
            libelle="Natural key", code="natural_key"
        )
        assert (
            SousCategorieObjet.objects.get_by_natural_key("natural_key").pk
            == some_sous_categorie.pk
        )
