import json

import pytest
from django.core.files.base import ContentFile

from qfdmo.models import CarteConfig, GroupeActionConfig
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

    def test_json_acteur_for_display_carte_config(self, displayed_acteur):
        carte_config = CarteConfig.objects.create(
            nom="Une carte sur mesure", slug="une-carte-sur-mesure"
        )
        groupe_action_config = GroupeActionConfig.objects.create(
            icon=ContentFile("<svg>some-icon</svg>", name="some-icon.svg"),
            carte_config=carte_config,
            acteur_type=displayed_acteur.acteur_type,
        )
        acteur_for_display = json.loads(
            displayed_acteur.json_acteur_for_display(carte_config=carte_config)
        )

        assert "icon" not in acteur_for_display
        assert acteur_for_display["iconFile"] == groupe_action_config.icon.url
