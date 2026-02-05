from django.core.management.base import BaseCommand

from qfdmd.models import Synonyme


class Command(BaseCommand):
    help = "Sync all Synonyme objects to SearchTerm entries"

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Show what would be done without making changes",
        )

    def handle(self, *args, **options):
        dry_run = options["dry_run"]

        synonymes = Synonyme.objects.all()
        total = synonymes.count()

        self.stdout.write(f"Found {total} Synonyme objects to sync")

        if dry_run:
            self.stdout.write(
                self.style.WARNING("Dry run mode - no changes will be made")
            )

        created_count = 0
        updated_count = 0
        error_count = 0

        for i, synonyme in enumerate(synonymes.iterator(), 1):
            if i % 100 == 0:
                self.stdout.write(f"Processing {i}/{total}...")

            try:
                if not dry_run:
                    from search.models import SearchTerm

                    search_term, created = SearchTerm.sync_from_object(synonyme)
                    if created:
                        created_count += 1
                    else:
                        updated_count += 1
                else:
                    self.stdout.write(
                        f"  Would sync: {synonyme.nom} -> {synonyme.get_absolute_url()}"
                    )
                    created_count += 1

            except Exception as e:
                error_count += 1
                self.stdout.write(
                    self.style.ERROR(f"Error syncing {synonyme.nom}: {e}")
                )

        self.stdout.write("")
        self.stdout.write(self.style.SUCCESS("Sync completed:"))
        self.stdout.write(f"  Created: {created_count}")
        self.stdout.write(f"  Updated: {updated_count}")
        self.stdout.write(f"  Errors: {error_count}")

        if not dry_run:
            self.stdout.write("")
            self.stdout.write(
                self.style.WARNING(
                    "Remember to run 'python manage.py update_index' to"
                    " update the search index"
                )
            )
