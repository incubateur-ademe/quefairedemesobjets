from qfdmo.models import CodeAsNaturalKeyModel, DataLicense, Source
from unit_tests.qfdmo.acteur_factory import SourceFactory


class TestSourceCodeAsNaturalKeyHeritage:
    def test_natural(self):
        assert CodeAsNaturalKeyModel in Source.mro()

    def test_default_license(self):
        assert SourceFactory.build().licence == DataLicense.NO_LICENSE
