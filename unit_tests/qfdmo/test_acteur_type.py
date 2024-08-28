from qfdmo.models import ActeurType, CodeAsNaturalKeyModel


class TestEntiteTypeNomAsNaturalKeyHeritage:
    def test_natural(self):
        assert CodeAsNaturalKeyModel in ActeurType.mro()
