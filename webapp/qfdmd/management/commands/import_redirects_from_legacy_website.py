import csv
from pathlib import Path

from django.core.management.base import BaseCommand
from wagtail.contrib.redirects.models import Redirect
from wagtail.models import Page


class Command(BaseCommand):
    help = "Import legacy Redirects"

    def add_arguments(self, parser):
        parser.add_argument(
            "csv_path", type=Path, help="Path to the redirects CSV file"
        )

    def handle(self, *args, **options):
        csv_path = options["csv_path"]

        created = 0
        skipped = 0
        errors = 0

        with open(csv_path, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                old_path = row["Depuis"].strip()
                page_id_str = row["Cible quefairedemesdechets.fr (id de page)"].strip()

                if not old_path or not page_id_str:
                    skipped += 1
                    continue

                try:
                    page_id = int(page_id_str)
                except ValueError:
                    self.stderr.write(
                        f"Invalid page ID '{page_id_str}' for path '{old_path}',"
                        " skipping."
                    )
                    errors += 1
                    continue

                try:
                    page = Page.objects.get(id=page_id)
                except Page.DoesNotExist:
                    self.stderr.write(
                        f"Page ID {page_id} not found for path '{old_path}', skipping."
                    )
                    errors += 1
                    continue

                _, was_created = Redirect.objects.update_or_create(
                    old_path=Redirect.normalise_path(old_path),
                    defaults={"redirect_page": page},
                )
                if was_created:
                    created += 1
                else:
                    skipped += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Done: {created} created, {skipped} skipped, {errors} errors."
            )
        )
