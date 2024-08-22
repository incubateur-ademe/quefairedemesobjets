from factory import Sequence
from factory.django import DjangoModelFactory as Factory

from qfdmo.models.action import Action, ActionDirection, GroupeAction


class ActionDirectionFactory(Factory):
    class Meta:
        model = ActionDirection
        django_get_or_create = ("code",)

    code = Sequence(lambda n: "jai" if n % 2 == 0 else "jecherche")
    libelle = Sequence(lambda n: "J'ai" if n % 2 == 0 else "Je cherche")
    order = Sequence(lambda n: n + 1)


class ActionFactory(Factory):
    class Meta:
        model = Action
        django_get_or_create = ("code",)

    code = "action"
    libelle = "Action"
    order = Sequence(lambda n: n + 1)


class GroupeActionFactory(Factory):
    class Meta:
        model = GroupeAction
        django_get_or_create = ("code",)

    code = "groupeaction"
    order = Sequence(lambda n: n + 1)
