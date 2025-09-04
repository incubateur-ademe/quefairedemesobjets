import pytest

from unit_tests.qfdmo.acteur_factory import (
    DisplayedActeurFactory,
    DisplayedPropositionServiceFactory,
)
from unit_tests.qfdmo.action_factory import (
    ActionDirectionFactory,
    ActionFactory,
    GroupeActionFactory,
)


@pytest.mark.django_db
class TestCarteConfig:
    @pytest.fixture
    def displayed_acteur(self):
        displayed_acteur = DisplayedActeurFactory()
        direction = ActionDirectionFactory()
        groupe_action = GroupeActionFactory(
            icon="icon-groupe_action",
            order=1,
        )
        action = ActionFactory(
            icon="icon-actionjai1",
            groupe_action=groupe_action,
            order=1,
        )
        action.directions.add(direction)
        DisplayedPropositionServiceFactory(action=action, acteur=displayed_acteur)
        return displayed_acteur
