from factory import LazyFunction, Sequence
from factory.django import DjangoModelFactory as Factory

from qfdmo.models.action import Action, Direction, GroupeAction


class ActionFactory(Factory):
    class Meta:
        model = Action
        django_get_or_create = ("code",)

    code = "action"
    libelle = "Action"
    order = Sequence(lambda n: n + 1)
    direction_codes = LazyFunction(lambda: [Direction.J_AI.value])


class GroupeActionFactory(Factory):
    class Meta:
        model = GroupeAction
        django_get_or_create = ("code",)

    code = "groupeaction"
    order = Sequence(lambda n: n + 1)
