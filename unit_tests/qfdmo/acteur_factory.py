import factory.fuzzy
from django.contrib.gis.geos import Point
from factory import SubFactory
from factory.django import DjangoModelFactory as Factory

from qfdmo.models import (
    Acteur,
    ActeurService,
    ActeurType,
    DisplayedActeur,
    DisplayedPropositionService,
    LabelQualite,
    PropositionService,
    Source,
)
from unit_tests.qfdmo.action_factory import ActionFactory


class SourceFactory(Factory):
    class Meta:
        model = Source

    afficher = True


class LabelQualiteFactory(Factory):
    class Meta:
        model = LabelQualite

    afficher = True


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


class DisplayedActeurFactory(Factory):
    class Meta:
        model = DisplayedActeur

    identifiant_unique = factory.fuzzy.FuzzyText(length=10)
    nom = "Test Object 1"
    location = Point(0, 0)
    acteur_type = SubFactory(ActeurTypeFactory)
    source = SubFactory(SourceFactory)


class ActeurServiceFactory(Factory):
    class Meta:
        model = ActeurService

    code = "service"


class PropositionServiceFactory(Factory):
    class Meta:
        model = PropositionService

    acteur_service = SubFactory(ActeurServiceFactory)
    action = SubFactory(ActionFactory)
    acteur = SubFactory(ActeurFactory)


class DisplayedPropositionServiceFactory(Factory):
    class Meta:
        model = DisplayedPropositionService

    acteur_service = SubFactory(ActeurServiceFactory)
    action = SubFactory(ActionFactory)
    acteur = SubFactory(DisplayedActeurFactory)
