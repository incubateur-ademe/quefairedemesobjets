from qfdmo.models import EntiteType, NomAsNaturalKeyModel


class TestEntiteTypeNomAsNaturalKeyHeritage:
    def test_natural(self):
        assert NomAsNaturalKeyModel in EntiteType.mro()
