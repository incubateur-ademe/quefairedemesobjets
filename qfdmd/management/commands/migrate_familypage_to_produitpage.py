"""
Management command to migrate FamilyPage instances to ProduitPage.

This command:
1. Sets est_famille=True on all FamilyPage instances
2. Updates their content_type from FamilyPage to ProduitPage

Usage:
    python manage.py migrate_familypage_to_produitpage --dry-run  # Preview changes
    python manage.py migrate_familypage_to_produitpage            # Apply changes
"""

from django.contrib.contenttypes.models import ContentType
from django.core.management.base import BaseCommand
from django.db import transaction
from wagtail.models import Page

from qfdmd.models import ProduitPage


class Command(BaseCommand):
    help = "Migrate FamilyPage instances to ProduitPage by updating content_type"

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Preview changes without applying them",
        )

    def handle(self, *args, **options):
        dry_run = options["dry_run"]

        if dry_run:
            self.stdout.write(self.style.WARNING("DRY RUN - No changes will be made\n"))

        # Get content types
        try:
            familypage_ct = ContentType.objects.get(
                app_label="qfdmd", model="familypage"
            )
        except ContentType.DoesNotExist:
            self.stdout.write(
                self.style.SUCCESS(
                    "FamilyPage content type does not exist. "
                    "Migration may have already been completed."
                )
            )
            return

        try:
            produitpage_ct = ContentType.objects.get(
                app_label="qfdmd", model="produitpage"
            )
        except ContentType.DoesNotExist:
            self.stdout.write(
                self.style.ERROR(
                    "ProduitPage content type does not exist. "
                    "Cannot proceed with migration."
                )
            )
            return

        self.stdout.write(f"FamilyPage content_type_id: {familypage_ct.id}")
        self.stdout.write(f"ProduitPage content_type_id: {produitpage_ct.id}")
        self.stdout.write("")

        # Find all pages with FamilyPage content type
        familypage_pages = Page.objects.filter(content_type=familypage_ct)
        familypage_count = familypage_pages.count()
        familypage_ids = list(familypage_pages.values_list("id", flat=True))

        self.stdout.write(f"Found {familypage_count} FamilyPage instance(s)")

        if familypage_count > 0:
            self.stdout.write("\nPages to migrate:")
            for page in familypage_pages:
                self.stdout.write(
                    f"  - [{page.id}] {page.title} (path: {page.url_path})"
                )

        if dry_run:
            self.stdout.write(
                self.style.WARNING("\nDRY RUN - Would perform the following actions:")
            )
            self.stdout.write(
                f"  1. Set est_famille=True on {familypage_count} page(s)"
            )
            self.stdout.write(
                f"  2. Update content_type from FamilyPage to ProduitPage "
                f"on {familypage_count} page(s)"
            )
            return

        if familypage_count == 0:
            self.stdout.write(
                self.style.SUCCESS("\nNo FamilyPage instances to migrate.")
            )
            return

        # Perform the migration
        with transaction.atomic():
            # 1. Set est_famille=True for pages that are FamilyPage
            updated_famille = ProduitPage.objects.filter(
                page_ptr_id__in=familypage_ids
            ).update(est_famille=True)
            self.stdout.write(
                self.style.SUCCESS(
                    f"\nSet est_famille=True on {updated_famille} page(s)"
                )
            )

            # 2. Update content_type for all FamilyPage instances
            updated_ct = familypage_pages.update(content_type=produitpage_ct)
            self.stdout.write(
                self.style.SUCCESS(
                    f"Updated content_type to ProduitPage on {updated_ct} page(s)"
                )
            )

        self.stdout.write(self.style.SUCCESS("\nMigration completed successfully!"))
