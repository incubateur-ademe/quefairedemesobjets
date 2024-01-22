from factory import Sequence
from factory.django import DjangoModelFactory as Factory

from qfdmo.models.action import Action, ActionDirection


class ActionDirectionFactory(Factory):
    class Meta:
        model = ActionDirection
        django_get_or_create = ("nom",)

    nom = Sequence(lambda n: "jai" if n % 2 == 0 else "jecherche")
    nom_affiche = Sequence(lambda n: "J'ai" if n % 2 == 0 else "Je cherche")
    order = Sequence(lambda n: n + 1)


class ActionFactory(Factory):
    class Meta:
        model = Action
        django_get_or_create = ("nom",)

    nom = "action"
    nom_affiche = "Action"
    order = Sequence(lambda n: n + 1)
