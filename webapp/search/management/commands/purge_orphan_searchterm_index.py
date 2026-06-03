import argparse

from django.contrib.contenttypes.models import ContentType
from django.core.management.base import BaseCommand
from modelsearch.models import IndexEntry

from search.models import SearchTerm

# Chunk size for the object_id IN clause. The orphan set can hold tens of
# thousands of ids; a single unbounded IN clause risks a statement timeout
# (see django-modelsearch issue #58).
CHUNK_SIZE = 1000


def _chunked(values, size):
    for start in range(0, len(values), size):
        yield values[start : start + size]


class Command(BaseCommand):
    help = (
        "Purge orphan base IndexEntry rows for SearchTerms that have a more "
        "specific child (Synonyme, SearchTag, ProduitPageSearchTerm). These "
        "rows were written before get_indexed_objects() excluded them and are "
        "never cleaned up by rebuild_modelsearch_index, because its stale "
        "detection only removes entries whose underlying row no longer exists. "
        "Leaving them in place duplicates results when a term matches via a "
        "variante de recherche. Should be run once after deploying the "
        "get_indexed_objects() multi-table inheritance fix."
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

        # ids of SearchTerm rows that have a more specific child. Their base
        # IndexEntry (content_type=SearchTerm) is the orphan we want to remove;
        # the child's own IndexEntry stays.
        child_ids = set()
        for child_model in (Synonyme, SearchTag, ProduitPageSearchTerm):
            child_ids.update(
                child_model.objects.values_list("searchterm_ptr_id", flat=True)
            )

        if not child_ids:
            self.stdout.write("No child SearchTerms found, nothing to purge.")
            return

        searchterm_ct = ContentType.objects.get_for_model(SearchTerm)
        # object_id is stored as text in the index table.
        object_ids = [str(pk) for pk in child_ids]

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
