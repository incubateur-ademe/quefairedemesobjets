import pytest

from qfdmo.models import Action, CodeAsNaturalKeyModel
from qfdmo.models.action import ActionDirection, get_actions_by_direction
from unit_tests.qfdmo.action_factory import ActionDirectionFactory, ActionFactory


class TestActionNomAsNaturalKeyHeritage:
    def test_natural(self):
        assert CodeAsNaturalKeyModel in Action.mro()

    def test_str(self):
        action = ActionFactory.build(code="My Code", libelle="My Libelle")
        assert str(action) == "My Libelle"


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


class TestCachedGetActionsByDirection:

    @pytest.mark.django_db
    def test_get_actions_by_direction_basic(self, action_directions, actions):

        assert [a["code"] for a in get_actions_by_direction()["first"]] == [
            "first_1",
            "first_2",
            "first_3",
            "first_second",
        ]
        assert [a["code"] for a in get_actions_by_direction()["second"]] == [
            "second_1",
            "second_2",
            "second_3",
            "first_second",
        ]

    @pytest.mark.django_db
    def test_get_actions_by_direction_order(self, action_directions, actions):
        Action.objects.filter(code="first_1").update(order=999)

        assert [a["code"] for a in get_actions_by_direction()["first"]] == [
            "first_2",
            "first_3",
            "first_second",
            "first_1",
        ]

    @pytest.mark.django_db
    def test_get_actions_by_direction_hidden(self, action_directions, actions):
        Action.objects.filter(code="first_1").update(afficher=False)

        assert [a["code"] for a in get_actions_by_direction()["first"]] == [
            "first_2",
            "first_3",
            "first_second",
        ]
