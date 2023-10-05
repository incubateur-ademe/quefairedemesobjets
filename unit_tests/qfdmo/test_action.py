import pytest

from qfdmo.models import Action, NomAsNaturalKeyModel


class TestActionNomAsNaturalKeyHeritage:
    def test_natural(self):
        assert NomAsNaturalKeyModel in Action.mro()

    @pytest.mark.django_db
    def test_serialize(self):
        action = Action.objects.create(
            nom="Test Object",
            lvao_id=123,
            nom_affiche="Test Objet Displayed",
            order=1,
        )
        assert action.serialize() == {
            "id": action.id,
            "description": None,
            "nom": "Test Object",
            "nom_affiche": "Test Objet Displayed",
            "order": 1,
            "lvao_id": 123,
            "couleur": "yellow-tournesol",
            "icon": None,
        }
