import pytest

from qfdmo.models import CategorieObjet, CodeAsNaturalKeyModel
from unit_tests.qfdmo.sscatobj_factory import CategorieObjetFactory


class TestCategorieObjetNomAsNaturalKeyHeritage:
    def test_natural(self):
        assert CodeAsNaturalKeyModel in CategorieObjet.mro()

    @pytest.mark.django_db
    def test_serialize(self):
        category = CategorieObjetFactory(libelle="Test Object", code="code_category")
        assert category.serialize() == {
            "id": category.id,
            "libelle": "Test Object",
            "code": "code_category",
        }
