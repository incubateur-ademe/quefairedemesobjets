from factory import SubFactory
from factory.django import DjangoModelFactory as Factory

from qfdmo.models.config import CarteConfig, GroupeActionConfig
from unit_tests.qfdmo.acteur_factory import ActeurTypeFactory
from unit_tests.qfdmo.action_factory import GroupeActionFactory


class CarteConfigFactory(Factory):
    class Meta:
        model = CarteConfig
        django_get_or_create = ("slug",)

    nom = "Carte sur mesure"
    slug = "carte-sur-mesure"


class GroupeActionConfigFactory(Factory):
    class Meta:
        model = GroupeActionConfig

    carte_config = SubFactory(CarteConfigFactory)
    groupe_action = SubFactory(GroupeActionFactory)
    acteur_type = SubFactory(ActeurTypeFactory)
