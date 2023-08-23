import pytest

from qfdmo.models import ActeurType, NomAsNaturalKeyModel


class TestEntiteTypeNomAsNaturalKeyHeritage:
    def test_natural(self):
        assert NomAsNaturalKeyModel in ActeurType.mro()

    @pytest.mark.django_db
    def test_serialize(self):
        acteur_type = ActeurType.objects.create(nom="Test Object", lvao_id=123)
        assert acteur_type.serialize() == {
            "id": acteur_type.id,
            "nom": "Test Object",
            "lvao_id": 123,
        }
