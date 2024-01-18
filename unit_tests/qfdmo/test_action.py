import pytest

from qfdmo.models import Action, NomAsNaturalKeyModel
from qfdmo.models.action import ActionDirection, CachedDirectionAction
from unit_tests.qfdmo.action_factory import ActionDirectionFactory


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


class TestCachedDirectionActionGetDirections:
    @pytest.fixture
    def action_directions(self):
        ActionDirection.objects.all().delete()
        ActionDirectionFactory(nom="first", nom_affiche="First")
        ActionDirectionFactory(nom="second", nom_affiche="Second")

    @pytest.mark.django_db
    @pytest.mark.parametrize(
        "first_direction,expected",
        [
            ("first", [{"nom": "first", "order": 1}, {"nom": "second", "order": 2}]),
            (
                "second",
                [{"nom": "second", "order": 2}, {"nom": "first", "order": 1}],
            ),
            (None, [{"nom": "first", "order": 1}, {"nom": "second", "order": 2}]),
        ],
    )
    def test_get_directions(self, first_direction, expected, action_directions):
        assert [
            {k: v for k, v in direction.items() if k in ["order", "nom"]}
            for direction in CachedDirectionAction.get_directions(
                first_direction=first_direction
            )
        ] == expected
