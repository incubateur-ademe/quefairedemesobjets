import random
import string

import factory.fuzzy
from django.contrib.gis.geos import Point
from factory import Faker, LazyFunction, SubFactory
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
    VueActeur,
)
from qfdmo.models.acteur import (
    PerimetreADomicile,
    RevisionActeur,
    RevisionPropositionService,
)
from unit_tests.qfdmo.action_factory import ActionFactory


def generate_random_word():
    length = 10
    characters = string.ascii_lowercase + string.digits + "_"
    return "".join(random.choice(characters) for _ in range(length))


class SourceFactory(Factory):
    class Meta:
        model = Source
        django_get_or_create = ("code",)

    libelle = Faker("word")
    code = LazyFunction(generate_random_word)
    afficher = True


class LabelQualiteFactory(Factory):
    class Meta:
        model = LabelQualite
        django_get_or_create = ("code",)

    libelle = Faker("word")
    code = LazyFunction(generate_random_word)
    afficher = True


class ActeurTypeFactory(Factory):
    class Meta:
        model = ActeurType
        django_get_or_create = ("code",)

    code = LazyFunction(generate_random_word)


class ActeurFactory(Factory):
    class Meta:
        model = Acteur

    nom = Faker("word")
    location = Point(1, 1)
    acteur_type = SubFactory(ActeurTypeFactory)
    source = SubFactory(SourceFactory)


class RevisionActeurFactory(Factory):
    class Meta:
        model = RevisionActeur

    nom = Faker("word")
    location = Point(2, 2)
    acteur_type = SubFactory(ActeurTypeFactory)
    source = SubFactory(SourceFactory)


class DisplayedActeurFactory(Factory):
    class Meta:
        model = DisplayedActeur

    identifiant_unique = factory.fuzzy.FuzzyText(length=10)
    nom = Faker("company")
    location = Point(3, 3)
    acteur_type = SubFactory(ActeurTypeFactory)


class VueActeurFactory(Factory):
    class Meta:
        model = VueActeur

    identifiant_unique = factory.fuzzy.FuzzyText(length=10)
    nom = Faker("word")
    location = Point(2, 2)
    acteur_type = SubFactory(ActeurTypeFactory)


class ActeurServiceFactory(Factory):
    class Meta:
        model = ActeurService
        django_get_or_create = ("code",)

    code = LazyFunction(generate_random_word)


class PropositionServiceFactory(Factory):
    class Meta:
        model = PropositionService

    action = SubFactory(ActionFactory)
    acteur = SubFactory(ActeurFactory)


class RevisionPropositionServiceFactory(Factory):
    class Meta:
        model = RevisionPropositionService

    action = SubFactory(ActionFactory)
    acteur = SubFactory(RevisionActeurFactory)


class DisplayedPropositionServiceFactory(Factory):
    class Meta:
        model = DisplayedPropositionService

    id = Faker("text", max_nb_chars=30)
    action = SubFactory(ActionFactory)
    acteur = SubFactory(DisplayedActeurFactory)


class PerimetreADomicileFactory(Factory):
    class Meta:
        model = PerimetreADomicile

    type = PerimetreADomicile.Type.KILOMETRIQUE
    valeur = str(Faker("random_int", min=10, max=99))
    acteur = SubFactory(ActeurFactory)
