import pytest

from qfdmo.models import Action, CodeAsNaturalKeyModel
from qfdmo.models.action import ActionDirection, CachedDirectionAction
from unit_tests.qfdmo.action_factory import ActionDirectionFactory, ActionFactory


class TestActionNomAsNaturalKeyHeritage:
    def test_natural(self):
        assert CodeAsNaturalKeyModel in Action.mro()

    @pytest.mark.django_db
    def test_serialize(self):
        action = Action.objects.create(
            code="Test Object",
            libelle="Test Objet Displayed",
            order=1,
        )
        assert action.serialize() == {
            "id": action.id,
            "description": None,
            "afficher": True,
            "code": "Test Object",
            "libelle": "Test Objet Displayed",
            "libelle_groupe": "",
            "groupe_action": None,
            "order": 1,
            "couleur": "yellow-tournesol",
            "icon": None,
        }


@pytest.fixture
def action_directions():
    ActionDirection.objects.all().delete()
    ActionDirectionFactory(code="first", libelle="First", order=1)
    ActionDirectionFactory(code="second", libelle="Second", order=2)


@pytest.fixture
def actions():
    first = ActionDirection.objects.get(code="first")
    second = ActionDirection.objects.get(code="second")

    ActionFactory(code="first_1").directions.add(first)
    ActionFactory(code="first_2").directions.add(first)
    ActionFactory(code="first_3").directions.add(first)
    ActionFactory(code="second_1").directions.add(second)
    ActionFactory(code="second_2").directions.add(second)
    ActionFactory(code="second_3").directions.add(second)
    ActionFactory(code="first_second").directions.add(first, second)


class TestCachedDirectionActionGetDirections:

    @pytest.mark.django_db
    @pytest.mark.parametrize(
        "first_direction,expected",
        [
            ("first", [{"code": "first", "order": 1}, {"code": "second", "order": 2}]),
            (
                "second",
                [{"code": "second", "order": 2}, {"code": "first", "order": 1}],
            ),
            (None, [{"code": "first", "order": 1}, {"code": "second", "order": 2}]),
        ],
    )
    def test_get_directions(self, first_direction, expected, action_directions):
        assert [
            {k: v for k, v in direction.items() if k in ["order", "code"]}
            for direction in CachedDirectionAction.get_directions(
                first_direction=first_direction
            )
        ] == expected


class TestCachedDirectionActionGetActionsByDirection:

    @pytest.mark.django_db
    def test_get_actions_by_direction_basic(self, action_directions, actions):
        CachedDirectionAction.reload_cache()

        assert [
            a["code"] for a in CachedDirectionAction.get_actions_by_direction()["first"]
        ] == ["first_1", "first_2", "first_3", "first_second"]
        assert [
            a["code"]
            for a in CachedDirectionAction.get_actions_by_direction()["second"]
        ] == ["second_1", "second_2", "second_3", "first_second"]

    @pytest.mark.django_db
    def test_get_actions_by_direction_order(self, action_directions, actions):
        Action.objects.filter(code="first_1").update(order=999)
        CachedDirectionAction.reload_cache()

        assert [
            a["code"] for a in CachedDirectionAction.get_actions_by_direction()["first"]
        ] == ["first_2", "first_3", "first_second", "first_1"]

    @pytest.mark.django_db
    def test_get_actions_by_direction_hidden(self, action_directions, actions):
        Action.objects.filter(code="first_1").update(afficher=False)
        CachedDirectionAction.reload_cache()

        assert [
            a["code"] for a in CachedDirectionAction.get_actions_by_direction()["first"]
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

        assert CachedDirectionAction._cached_actions_by_code is None

        CachedDirectionAction.get_actions_by_code()

        assert CachedDirectionAction._cached_actions_by_code is not None

    def test_reload_cache(self):
        CachedDirectionAction._cached_actions_by_direction = (
            "cached_actions_by_direction"
        )
        CachedDirectionAction._cached_actions_by_code = "cached_actions"
        CachedDirectionAction._cached_direction = "cached_direction"
        CachedDirectionAction._reparer_action_id = "reparer_action_id"

        CachedDirectionAction.reload_cache()

        assert CachedDirectionAction._cached_actions_by_direction is None
        assert CachedDirectionAction._cached_actions_by_code is None
        assert CachedDirectionAction._cached_direction is None
        assert CachedDirectionAction._reparer_action_id is None
