import pytest

from qfdmo.models.action import Direction
from unit_tests.qfdmo.acteur_factory import (
    DisplayedActeurFactory,
    DisplayedPropositionServiceFactory,
)
from unit_tests.qfdmo.action_factory import ActionFactory, GroupeActionFactory


@pytest.mark.django_db
class TestCarteConfig:
    @pytest.fixture
    def displayed_acteur(self):
        displayed_acteur = DisplayedActeurFactory()
        groupe_action = GroupeActionFactory(
            icon="icon-groupe_action",
            order=1,
        )
        action = ActionFactory(
            icon="icon-actionjai1",
            groupe_action=groupe_action,
            order=1,
            direction_codes=[Direction.J_AI.value],
        )
        DisplayedPropositionServiceFactory(action=action, acteur=displayed_acteur)
        return displayed_acteur
