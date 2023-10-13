import pytest

from qfdmo.models import NomAsNaturalKeyModel, SourceDonnee


class TestSourceDonneeNomAsNaturalKeyHeritage:
    def test_natural(self):
        assert NomAsNaturalKeyModel in SourceDonnee.mro()

    @pytest.mark.django_db
    def test_serialize(self):
        source = SourceDonnee.objects.create(
            nom="Test Object", logo="path/to/logo", afficher=True, url="path/to/source"
        )
        assert source.serialize() == {
            "id": source.id,
            "nom": "Test Object",
            "logo": "path/to/logo",
            "afficher": True,
            "url": "path/to/source",
        }
