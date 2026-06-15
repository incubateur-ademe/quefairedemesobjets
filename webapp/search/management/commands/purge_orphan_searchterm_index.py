import argparse

from django.contrib.contenttypes.models import ContentType
from django.core.management.base import BaseCommand
from modelsearch.models import IndexEntry

from search.models import SearchTerm

# Chunk the object_id IN clause to avoid a statement timeout on a large index.
CHUNK_SIZE = 1000


def _chunked(values, size):
    for start in range(0, len(values), size):
        yield values[start : start + size]


class Command(BaseCommand):
    help = (
        "Purge orphan base SearchTerm IndexEntry rows for objects that have a "
        "more specific child. rebuild_modelsearch_index does not remove them "
        "(django-modelsearch #58); leaving them duplicates search results when "
        "a term matches via a variante de recherche."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            help="Report what would be deleted without writing changes",
            action=argparse.BooleanOptionalAction,
            default=False,
        )

    def handle(self, *args, **options):
        from qfdmd.models import ProduitPageSearchTerm, SearchTag, Synonyme

        dry_run = options["dry_run"]

        # SearchTerm ids that have a more specific child; their base IndexEntry
        # is the orphan to remove. The child's own IndexEntry stays.
        child_ids = set()
        for child_model in (Synonyme, SearchTag, ProduitPageSearchTerm):
            child_ids.update(
                child_model.objects.values_list("searchterm_ptr_id", flat=True)
            )

        if not child_ids:
            self.stdout.write("No child SearchTerms found, nothing to purge.")
            return

        searchterm_ct = ContentType.objects.get_for_model(SearchTerm)
        object_ids = [str(pk) for pk in child_ids]  # object_id is text in the index

        total = 0
        for chunk in _chunked(object_ids, CHUNK_SIZE):
            orphans = IndexEntry.objects.filter(
                content_type=searchterm_ct,
                object_id__in=chunk,
            )
            if dry_run:
                total += orphans.count()
            else:
                deleted, _ = orphans.delete()
                total += deleted

        verb = "Would delete" if dry_run else "Deleted"
        self.stdout.write(
            self.style.SUCCESS(f"{verb} {total} orphan SearchTerm IndexEntry rows.")
        )
