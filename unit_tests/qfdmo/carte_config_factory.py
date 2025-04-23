from factory.django import DjangoModelFactory as Factory

from qfdmo.models.config import CarteConfig


class CarteConfigFactory(Factory):
    class Meta:
        model = CarteConfig

    nom = "Carte sur mesure"
    slug = "carte-sur-mesure"
