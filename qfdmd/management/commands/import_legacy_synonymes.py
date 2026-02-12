from django.core.management.base import BaseCommand

from qfdmd.models import ProduitPage, ProduitPageSearchTerm, Synonyme
from search.models import SearchTerm


class Command(BaseCommand):
    help = "Import legacy synonymes as SearchTags for all ProduitPages "

    def handle(self, *args, **options):
        all_pages = ProduitPage.objects.all()

        for synonyme in Synonyme.objects.all():
            search_term = SearchTerm.objects.create()
            synonyme.searchterm_ptr_id = search_term.id
            synonyme.save(update_fields=["searchterm_ptr_id"])

        for page in all_pages.iterator():
            ProduitPageSearchTerm.objects.update_or_create(
                produit_page=page,
                defaults={"searchable_title": page.titre_phrase or page.title},
            )
