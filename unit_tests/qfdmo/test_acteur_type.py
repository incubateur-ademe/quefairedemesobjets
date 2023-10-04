import pytest

from qfdmo.models import ActeurType, NomAsNaturalKeyModel


class TestEntiteTypeNomAsNaturalKeyHeritage:
    def test_natural(self):
        assert NomAsNaturalKeyModel in ActeurType.mro()

    @pytest.mark.django_db
    def test_serialize(self):
        acteur_type = ActeurType.objects.create(
            nom="Test Object", nom_affiche="Test Object Affiche", lvao_id=123
        )
        print(acteur_type.serialize())
        assert acteur_type.serialize() == {
            "id": acteur_type.id,
            "nom": "Test Object",
            "nom_affiche": "Test Object Affiche",
            "lvao_id": 123,
        }
