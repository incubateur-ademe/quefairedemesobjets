from qfdmo.models import CategorieObjet, NomAsNaturalKeyModel


class TestCategorieObjetNomAsNaturalKeyHeritage:
    def test_natural(self):
        assert NomAsNaturalKeyModel in CategorieObjet.mro()
