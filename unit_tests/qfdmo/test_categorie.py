from qfdmo.models import CategorieObjet, CodeAsNaturalKeyModel


class TestCategorieObjetNomAsNaturalKeyHeritage:
    def test_natural(self):
        assert CodeAsNaturalKeyModel in CategorieObjet.mro()
