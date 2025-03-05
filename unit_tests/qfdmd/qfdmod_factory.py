from factory import Faker, SubFactory
from factory.django import DjangoModelFactory as Factory

from qfdmd.models import Lien, Produit, Synonyme


class LienFactory(Factory):
    class Meta:
        model = Lien
        django_get_or_create = ("url",)

    titre_du_lien = Faker("sentence", nb_words=3)
    url = Faker("url")


class ProduitFactory(Factory):
    class Meta:
        model = Produit
        django_get_or_create = ("nom",)

    id = Faker("pyint", min_value=1)  # Ajout d'un ID unique
    nom = Faker("sentence", nb_words=3)


class SynonymeFactory(Factory):
    class Meta:
        model = Synonyme
        django_get_or_create = ("nom",)

    nom = Faker("sentence", nb_words=3)
    produit = SubFactory(ProduitFactory)
