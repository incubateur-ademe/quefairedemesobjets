import factory.fuzzy
from django.contrib.gis.geos import Point
from factory import Faker, SubFactory
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
        django_get_or_create = ("code",)

    libelle = Faker("word")
    code = Faker("word")
    afficher = True


class LabelQualiteFactory(Factory):
    class Meta:
        model = LabelQualite
        django_get_or_create = ("code",)

    afficher = True
    code = "a code"


class ActeurTypeFactory(Factory):
    class Meta:
        model = ActeurType
        django_get_or_create = ("code",)

    code = Faker("word")


class ActeurFactory(Factory):
    class Meta:
        model = Acteur

    nom = "Test Object 1"
    location = Point(1, 1)
    acteur_type = SubFactory(ActeurTypeFactory)
    source = SubFactory(SourceFactory)


class DisplayedActeurFactory(Factory):
    class Meta:
        model = DisplayedActeur

    identifiant_unique = factory.fuzzy.FuzzyText(length=10)
    nom = "Test Object 1"
    location = Point(1, 1)
    acteur_type = SubFactory(ActeurTypeFactory)
    source = SubFactory(SourceFactory)


class ActeurServiceFactory(Factory):
    class Meta:
        model = ActeurService

    code = Faker("word")


class PropositionServiceFactory(Factory):
    class Meta:
        model = PropositionService

    action = SubFactory(ActionFactory)
    acteur = SubFactory(ActeurFactory)


class DisplayedPropositionServiceFactory(Factory):
    class Meta:
        model = DisplayedPropositionService

    action = SubFactory(ActionFactory)
    acteur = SubFactory(DisplayedActeurFactory)
