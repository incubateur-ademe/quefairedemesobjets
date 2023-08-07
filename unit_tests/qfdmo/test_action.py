from qfdmo.models import Action, NomAsNaturalKeyModel


class TestActionNomAsNaturalKeyHeritage:
    def test_natural(self):
        assert NomAsNaturalKeyModel in Action.mro()
