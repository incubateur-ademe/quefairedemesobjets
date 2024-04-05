import pytest

from qfdmo.models import CodeAsNaturalKeyModel, Source


class TestSourceCodeAsNaturalKeyHeritage:
    def test_natural(self):
        assert CodeAsNaturalKeyModel in Source.mro()

    @pytest.mark.django_db
    def test_serialize(self):
        source = Source.objects.create(
            libelle="Test Object",
            afficher=True,
            url="path/to/source",
            code="code_source",
        )
        assert source.serialize() == {
            "id": source.id,
            "libelle": "Test Object",
            "code": "code_source",
            "afficher": True,
            "url": "path/to/source",
            "logo_file": None,
        }
