from django.core.management.base import BaseCommand

from qfdmd.models import ProduitPage, ProduitPageSearchTerm


class Command(BaseCommand):
    help = "Import legacy synonymes as SearchTags for all ProduitPages "

    def handle(self, *args, **options):
        all_pages = ProduitPage.objects.all()

        for page in all_pages.iterator():
            ProduitPageSearchTerm.objects.update_or_create(
                produit_page=page,
                defaults={"searchable_title": page.titre_phrase or page.title},
            )
