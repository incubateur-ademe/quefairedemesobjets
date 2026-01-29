import factory
import wagtail_factories
from factory import Faker, SubFactory
from factory.django import DjangoModelFactory as Factory
from wagtail.models import Page

from qfdmd.models import Lien, Produit, ProduitIndexPage, ProduitPage, Synonyme


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

    nom = Faker("sentence", nb_words=3)


class SynonymeFactory(Factory):
    class Meta:
        model = Synonyme
        django_get_or_create = ("nom",)

    nom = Faker("sentence", nb_words=3)
    produit = SubFactory(ProduitFactory)


class PageFactory(wagtail_factories.PageFactory):
    """Factory for generic Wagtail Page with SEO fields."""

    class Meta:
        model = Page

    title = factory.Sequence(lambda n: f"Page {n}")
    slug = factory.Sequence(lambda n: f"page-{n}")
    seo_title = factory.LazyAttribute(lambda o: f"SEO Title - {o.title}")
    search_description = factory.LazyAttribute(
        lambda o: f"Description SEO de {o.title}"
    )


class ProduitIndexPageFactory(wagtail_factories.PageFactory):
    """Factory for ProduitIndexPage."""

    class Meta:
        model = ProduitIndexPage

    title = factory.Sequence(lambda n: f"Produits Index {n}")
    slug = factory.Sequence(lambda n: f"produits-index-{n}")


class ProduitPageFactory(wagtail_factories.PageFactory):
    """Factory for ProduitPage with SEO fields."""

    class Meta:
        model = ProduitPage

    title = factory.Sequence(lambda n: f"Produit {n}")
    slug = factory.Sequence(lambda n: f"produit-{n}")
    seo_title = factory.LazyAttribute(lambda o: f"Que faire de {o.title}")
    search_description = factory.LazyAttribute(
        lambda o: f"Découvrez comment recycler {o.title}"
    )
