from factory import Faker, LazyFunction, SubFactory
from factory.django import DjangoModelFactory as Factory

from qfdmo.models import CategorieObjet, Objet, SousCategorieObjet
from unit_tests.qfdmo.acteur_factory import generate_random_word


class CategorieObjetFactory(Factory):
    class Meta:
        model = CategorieObjet
        django_get_or_create = ("code",)

    code = LazyFunction(generate_random_word)
    libelle = Faker("word")


class SousCategorieObjetFactory(Factory):
    class Meta:
        model = SousCategorieObjet
        django_get_or_create = ("code",)

    code = LazyFunction(generate_random_word)
    libelle = Faker("word")
    categorie = SubFactory(CategorieObjetFactory)


class ObjetFactory(Factory):
    class Meta:
        model = Objet
        django_get_or_create = ("code",)

    code = LazyFunction(generate_random_word)
    libelle = Faker("word")
    sous_categorie = SubFactory(SousCategorieObjetFactory)
