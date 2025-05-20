from django.core.management.base import BaseCommand
from django.utils.text import slugify

from qfdmd.models import Produit, ProduitIndexPage, ProduitPage, Synonyme, SynonymePage


def create_wagtail_pages_for_produit():
    index_page = ProduitIndexPage.objects.first()

    for produit in Produit.objects.all():
        produit_page = ProduitPage(
            produit=produit,
            title=produit.nom,
            slug=slugify(produit.slug),
        )
        index_page.add_child(instance=produit_page)
        produit_page.save_revision
        print(f"{produit_page=} created")

    for synonyme in Synonyme.objects.all():
        synonyme_page = SynonymePage(title=synonyme.nom, slug=slugify(synonyme.slug))
        synonyme.produit.produit_page.add_child(instance=synonyme_page)
        synonyme_page.save_revision()
        print(f"{synonyme_page=} created")


class Command(BaseCommand):
    help = "Generate Wagtail pages from existing produit and synonyme"

    def handle(self, *args, **options):
        create_wagtail_pages_for_produit()
