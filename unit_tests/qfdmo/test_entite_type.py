from qfdmo.models import ActeurType, NomAsNaturalKeyModel


class TestEntiteTypeNomAsNaturalKeyHeritage:
    def test_natural(self):
        assert NomAsNaturalKeyModel in ActeurType.mro()
