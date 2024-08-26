from qfdmo.models import CodeAsNaturalKeyModel, Source


class TestSourceCodeAsNaturalKeyHeritage:
    def test_natural(self):
        assert CodeAsNaturalKeyModel in Source.mro()
