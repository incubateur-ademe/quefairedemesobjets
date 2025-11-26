import factory
from factory import Faker, SubFactory
from factory.django import DjangoModelFactory as Factory

from data.models.suggestion import (
    Suggestion,
    SuggestionCohorte,
    SuggestionGroupe,
    SuggestionUnitaire,
)


class SuggestionCohorteFactory(Factory):
    class Meta:
        model = SuggestionCohorte

    identifiant_action = Faker("word")
    identifiant_execution = Faker("iso8601")
    type_action = ""


class SuggestionFactory(Factory):
    class Meta:
        model = Suggestion

    suggestion_cohorte = SubFactory(SuggestionCohorteFactory)


class SuggestionGroupeFactory(Factory):
    class Meta:
        model = SuggestionGroupe

    suggestion_cohorte = SubFactory(SuggestionCohorteFactory)


class SuggestionUnitaireFactory(Factory):
    class Meta:
        model = SuggestionUnitaire

    suggestion_groupe = SubFactory(SuggestionGroupeFactory)
    champs = factory.LazyAttribute(lambda _: [])
    valeurs = factory.LazyAttribute(lambda _: [])
