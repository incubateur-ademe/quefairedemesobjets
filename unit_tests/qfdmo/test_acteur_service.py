import pytest

from qfdmo.models import ActeurService, NomAsNaturalKeyModel


class TestEntiteServiceNomAsNaturalKeyHeritage:
    def test_natural(self):
        assert NomAsNaturalKeyModel in ActeurService.mro()

    @pytest.mark.django_db
    def test_serialize(self):
        acteur_service = ActeurService.objects.create(nom="Test Object", lvao_id=123)
        assert acteur_service.serialize() == {
            "id": acteur_service.id,
            "nom": "Test Object",
            "libelle": None,
            "lvao_id": 123,
        }
