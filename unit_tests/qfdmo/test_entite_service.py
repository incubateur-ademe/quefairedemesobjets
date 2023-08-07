from qfdmo.models import EntiteService, NomAsNaturalKeyModel


class TestEntiteServiceNomAsNaturalKeyHeritage:
    def test_natural(self):
        assert NomAsNaturalKeyModel in EntiteService.mro()
