from factory import Faker
from factory.django import DjangoModelFactory as Factory

from qfdmo.models.config import CarteConfig


class CarteConfigFactory(Factory):
    class Meta:
        model = CarteConfig

    nom = Faker("word")
    slug = Faker("word")
