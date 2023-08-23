import pytest

from qfdmo.models import CategorieObjet, NomAsNaturalKeyModel


class TestCategorieObjetNomAsNaturalKeyHeritage:
    def test_natural(self):
        assert NomAsNaturalKeyModel in CategorieObjet.mro()

    @pytest.mark.django_db
    def test_serialize(self):
        category = CategorieObjet.objects.create(nom="Test Object")
        assert category.serialize() == {"id": category.id, "nom": "Test Object"}
