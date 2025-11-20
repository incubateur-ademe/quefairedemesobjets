import pytest
from django.core.cache import cache

from qfdmo.models import Action, CodeAsNaturalKeyModel
from qfdmo.models.action import Direction, get_actions_by_direction
from unit_tests.qfdmo.action_factory import ActionFactory


class TestActionNomAsNaturalKeyHeritage:
    def test_natural(self):
        assert CodeAsNaturalKeyModel in Action.mro()

    def test_str(self):
        action = ActionFactory.build(code="My Code", libelle="My Libelle")
        assert str(action) == "My Libelle"


@pytest.fixture
def actions():
    Action.objects.all().delete()
    cache.clear()

    ActionFactory(code="jai_1", order=1, direction_codes=[Direction.J_AI.value])
    ActionFactory(code="jai_2", order=2, direction_codes=[Direction.J_AI.value])
    ActionFactory(code="jai_3", order=3, direction_codes=[Direction.J_AI.value])
    ActionFactory(
        code="jecherche_1",
        order=1,
        direction_codes=[Direction.JE_CHERCHE.value],
    )
    ActionFactory(
        code="jecherche_2",
        order=2,
        direction_codes=[Direction.JE_CHERCHE.value],
    )
    ActionFactory(
        code="jecherche_3",
        order=3,
        direction_codes=[Direction.JE_CHERCHE.value],
    )
    ActionFactory(
        code="both",
        order=4,
        direction_codes=[
            Direction.J_AI.value,
            Direction.JE_CHERCHE.value,
        ],
    )


class TestCachedGetActionsByDirection:

    @pytest.mark.django_db
    def test_get_actions_by_direction_basic(self, actions):
        assert [
            a["code"] for a in get_actions_by_direction()[Direction.J_AI.value]
        ] == [
            "jai_1",
            "jai_2",
            "jai_3",
            "both",
        ]
        assert [
            a["code"] for a in get_actions_by_direction()[Direction.JE_CHERCHE.value]
        ] == [
            "jecherche_1",
            "jecherche_2",
            "jecherche_3",
            "both",
        ]

    @pytest.mark.django_db
    def test_get_actions_by_direction_order(self, actions):
        Action.objects.filter(code="jai_1").update(order=999)

        assert [
            a["code"] for a in get_actions_by_direction()[Direction.J_AI.value]
        ] == [
            "jai_2",
            "jai_3",
            "both",
            "jai_1",
        ]

    @pytest.mark.django_db
    def test_get_actions_by_direction_hidden(self, actions):
        Action.objects.filter(code="jai_1").update(afficher=False)

        assert [
            a["code"] for a in get_actions_by_direction()[Direction.J_AI.value]
        ] == [
            "jai_2",
            "jai_3",
            "both",
        ]
