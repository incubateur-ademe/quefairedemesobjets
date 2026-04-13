import csv
from pathlib import Path

from django.core.management.base import BaseCommand
from qfdmd.models import HomePage
from wagtail.contrib.redirects.models import Redirect
from wagtail.models import Page, Site


def create_or_update_site_vitrine():
    homepage = HomePage.objects.first()
    site, _ = Site.objects.get_or_create(
        hostname="longuevieauxobjets.ademe.fr",
        defaults={
            "root_page": homepage,
            "hostname": "longuevieauxobjets.ademe.fr",
            "port": 443,
            "site_name": "Ancien site vitrine",
        },
    )
    return site


def page_exists_at_path(old_path: str) -> bool:
    """Return True if a Wagtail page is already served at the given URL path."""
    current_site = Site.objects.filter(is_default_site=True).first()
    if current_site is None:
        return False
    root_url_path = current_site.root_page.url_path
    normalized = old_path.strip("/")
    candidate_url_path = f"{root_url_path.rstrip('/')}/{normalized}/"
    return Page.objects.filter(url_path=candidate_url_path, live=True).exists()


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

        site = create_or_update_site_vitrine()

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

                if page_exists_at_path(old_path):
                    self.stderr.write(
                        self.style.WARNING(
                            f"Warning: a live page already exists at '{old_path}',"
                            " the redirect may be ignored by Wagtail."
                        )
                    )

                _, was_created = Redirect.objects.update_or_create(
                    old_path=Redirect.normalise_path(old_path),
                    site=site,
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
