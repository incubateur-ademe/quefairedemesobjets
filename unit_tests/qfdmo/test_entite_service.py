from qfdmo.models import ActeurService, NomAsNaturalKeyModel


class TestEntiteServiceNomAsNaturalKeyHeritage:
    def test_natural(self):
        assert NomAsNaturalKeyModel in ActeurService.mro()
