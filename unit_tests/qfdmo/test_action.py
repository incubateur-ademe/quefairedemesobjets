import pytest

from qfdmo.models import Action, NomAsNaturalKeyModel
from qfdmo.models.action import ActionDirection, CachedDirectionAction
from unit_tests.qfdmo.action_factory import ActionDirectionFactory, ActionFactory


class TestActionNomAsNaturalKeyHeritage:
    def test_natural(self):
        assert NomAsNaturalKeyModel in Action.mro()

    @pytest.mark.django_db
    def test_serialize(self):
        action = Action.objects.create(
            nom="Test Object",
            lvao_id=123,
            libelle="Test Objet Displayed",
            order=1,
        )
        assert action.serialize() == {
            "id": action.id,
            "description": None,
            "afficher": True,
            "nom": "Test Object",
            "libelle": "Test Objet Displayed",
            "order": 1,
            "lvao_id": 123,
            "couleur": "yellow-tournesol",
            "icon": None,
        }


@pytest.fixture
def action_directions():
    ActionDirection.objects.all().delete()
    ActionDirectionFactory(nom="first", libelle="First", order=1)
    ActionDirectionFactory(nom="second", libelle="Second", order=2)


@pytest.fixture
def actions():
    first = ActionDirection.objects.get(nom="first")
    second = ActionDirection.objects.get(nom="second")

    ActionFactory(nom="first_1").directions.add(first)
    ActionFactory(nom="first_2").directions.add(first)
    ActionFactory(nom="first_3").directions.add(first)
    ActionFactory(nom="second_1").directions.add(second)
    ActionFactory(nom="second_2").directions.add(second)
    ActionFactory(nom="second_3").directions.add(second)
    ActionFactory(nom="first_second").directions.add(first, second)


class TestCachedDirectionActionGetDirections:

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


class TestCachedDirectionActionGetActionsByDirection:

    @pytest.mark.django_db
    def test_get_actions_by_direction_basic(self, action_directions, actions):
        CachedDirectionAction.reload_cache()

        assert [
            a["nom"] for a in CachedDirectionAction.get_actions_by_direction()["first"]
        ] == ["first_1", "first_2", "first_3", "first_second"]
        assert [
            a["nom"] for a in CachedDirectionAction.get_actions_by_direction()["second"]
        ] == ["second_1", "second_2", "second_3", "first_second"]

    @pytest.mark.django_db
    def test_get_actions_by_direction_order(self, action_directions, actions):
        Action.objects.filter(nom="first_1").update(order=999)
        CachedDirectionAction.reload_cache()

        assert [
            a["nom"] for a in CachedDirectionAction.get_actions_by_direction()["first"]
        ] == ["first_2", "first_3", "first_second", "first_1"]

    @pytest.mark.django_db
    def test_get_actions_by_direction_hidden(self, action_directions, actions):
        Action.objects.filter(nom="first_1").update(afficher=False)
        CachedDirectionAction.reload_cache()

        assert [
            a["nom"] for a in CachedDirectionAction.get_actions_by_direction()["first"]
        ] == ["first_2", "first_3", "first_second"]


class TestCachedDirectionActionReloadCache:

    @pytest.mark.django_db
    def test__reparer_action_id(self, action_directions, actions):
        CachedDirectionAction.reload_cache()

        assert CachedDirectionAction._reparer_action_id is None

        CachedDirectionAction.get_reparer_action_id()

        assert CachedDirectionAction._reparer_action_id is not None

    @pytest.mark.django_db
    def test__cached_direction(self, action_directions, actions):
        CachedDirectionAction.reload_cache()

        assert CachedDirectionAction._cached_direction is None

        CachedDirectionAction.get_directions()

        assert CachedDirectionAction._cached_direction is not None

    @pytest.mark.django_db
    def test__cached_actions_by_direction(self, action_directions, actions):
        CachedDirectionAction.reload_cache()

        assert CachedDirectionAction._cached_actions_by_direction is None

        CachedDirectionAction.get_actions_by_direction()

        assert CachedDirectionAction._cached_actions_by_direction is not None

    @pytest.mark.django_db
    def test__cached_actions(self, action_directions, actions):
        CachedDirectionAction.reload_cache()

        assert CachedDirectionAction._cached_actions is None

        CachedDirectionAction.get_actions()

        assert CachedDirectionAction._cached_actions is not None

    def test_reload_cache(self):
        CachedDirectionAction._cached_actions_by_direction = (
            "cached_actions_by_direction"
        )
        CachedDirectionAction._cached_actions = "cached_actions"
        CachedDirectionAction._cached_direction = "cached_direction"
        CachedDirectionAction._reparer_action_id = "reparer_action_id"

        CachedDirectionAction.reload_cache()

        assert CachedDirectionAction._cached_actions_by_direction is None
        assert CachedDirectionAction._cached_actions is None
        assert CachedDirectionAction._cached_direction is None
        assert CachedDirectionAction._reparer_action_id is None
