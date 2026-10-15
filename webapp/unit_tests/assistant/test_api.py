"""API v1 endpoints of the assistant's screens."""

import pytest
from django.contrib.gis.geos import Point

from qfdmo.models.acteur import DataLicense
from unit_tests.qfdmo.acteur_factory import (
    DisplayedActeurFactory,
    DisplayedPropositionServiceFactory,
    SourceFactory,
)
from unit_tests.qfdmo.action_factory import ActionFactory, GroupeActionFactory

pytestmark = pytest.mark.django_db

PARIS = {"latitude": "48.8534", "longitude": "2.3488"}
PARIS_POINT = Point(2.3488, 48.8534, srid=4326)


@pytest.fixture
def reparer():
    groupe = GroupeActionFactory(code="reparer", libelle_court="Réparer")
    return ActionFactory(code="reparer", groupe_action=groupe)


def place(action, *, licence=DataLicense.OPEN_LICENSE, at=PARIS_POINT):
    acteur = DisplayedActeurFactory(location=at)
    acteur.sources.add(SourceFactory(licence=licence))
    DisplayedPropositionServiceFactory(acteur=acteur, action=action)
    return acteur
