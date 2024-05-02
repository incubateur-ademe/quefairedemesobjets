import pytest

from qfdmo.models import ActeurService, CodeAsNaturalKeyModel


class TestEntiteServiceNomAsNaturalKeyHeritage:
    def test_natural(self):
        assert CodeAsNaturalKeyModel in ActeurService.mro()

    @pytest.mark.django_db
    def test_serialize(self):
        acteur_service = ActeurService.objects.create(code="Test Object")
        assert acteur_service.serialize() == {
            "id": acteur_service.id,
            "code": "Test Object",
            "libelle": None,
        }
