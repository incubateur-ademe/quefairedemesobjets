from django.contrib.gis.geos import Point
from factory import SubFactory
from factory.django import DjangoModelFactory as Factory

from qfdmo.models import Acteur, ActeurType, Source
from qfdmo.models.acteur import ActeurService, PropositionService
from unit_tests.qfdmo.action_factory import ActionFactory


class SourceFactory(Factory):
    class Meta:
        model = Source


class ActeurTypeFactory(Factory):
    class Meta:
        model = ActeurType


class ActeurFactory(Factory):
    class Meta:
        model = Acteur

    nom = "Test Object 1"
    location = Point(0, 0)
    acteur_type = SubFactory(ActeurTypeFactory)
    source = SubFactory(SourceFactory)


class ActeurServiceFactory(Factory):
    class Meta:
        model = ActeurService

    nom = "service"


class PropositionServiceFactory(Factory):
    class Meta:
        model = PropositionService

    acteur_service = SubFactory(ActeurServiceFactory)
    action = SubFactory(ActionFactory)
    acteur = SubFactory(ActeurFactory)
