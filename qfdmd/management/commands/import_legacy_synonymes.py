from django.core.management.base import BaseCommand

from qfdmd.models import ProduitPage
from qfdmd.views import _collect_synonymes_for_page, _execute_import


class Command(BaseCommand):
    help = (
        "Import legacy synonymes as SearchTags for all ProduitPages "
        "that have not been migrated yet."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Show what would be imported without making changes.",
        )

    def handle(self, *args, **options):
        dry_run = options["dry_run"]

        pages = list(ProduitPage.objects.filter(migree_depuis_synonymes_legacy=False))

        if not pages:
            self.stdout.write("No unmigrated ProduitPages found.")
            return

        self.stdout.write(f"Found {len(pages)} unmigrated ProduitPage(s).")

        total_imported = 0

        for page in pages:
            all_synonymes = _collect_synonymes_for_page(page)
            count = len(all_synonymes)

            if dry_run:
                self.stdout.write(
                    f"  [DRY RUN] Page {page.pk} ({page.title}): "
                    f"{count} synonyme(s) to import"
                )
                total_imported += count
                continue

            if all_synonymes:
                _execute_import(page, all_synonymes)

            page.legacy_synonymes.all().delete()
            page.legacy_produit.all().delete()
            page.legacy_synonymes_to_exclude.all().delete()
            page.migree_depuis_synonymes_legacy = True
            page.save(update_fields=["migree_depuis_synonymes_legacy"])

            self.stdout.write(
                f"  Page {page.pk} ({page.title}): {count} synonyme(s) imported"
            )
            total_imported += count

        if dry_run:
            self.stdout.write(
                f"\n[DRY RUN] Would import {total_imported} synonyme(s) "
                f"across {len(pages)} page(s)."
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(
                    f"\nDone. Imported {total_imported} synonyme(s) "
                    f"across {len(pages)} page(s)."
                )
            )
