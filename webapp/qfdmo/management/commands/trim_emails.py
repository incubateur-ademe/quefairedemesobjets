import argparse

from django.core.management.base import BaseCommand
from django.db import transaction
from django.db.models import Q
from django.db.models.functions import Trim
from qfdmo.models.acteur import Acteur, RevisionActeur


class Command(BaseCommand):
    help = "Strip leading and trailing whitespace from acteur emails"

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            help="Run command without writing changes to the database",
            action=argparse.BooleanOptionalAction,
            default=False,
        )

    def handle(self, *args, **options):
        dry_run = options["dry_run"]
        email_to_strip = Q(email__startswith=" ") | Q(email__endswith=" ")

        with transaction.atomic():
            results = []
            for model in (Acteur, RevisionActeur):
                qs = model.objects.filter(email_to_strip)
                emails = qs.values_list("email", flat=True)
                if dry_run:
                    count = qs.count()
                else:
                    count = qs.update(email=Trim("email"))
                results.append((model.__name__, count, emails))

        prefix = "[DRY-RUN] " if dry_run else ""
        for name, count, emails in results:
            self.stdout.write(
                self.style.SUCCESS(f"{prefix}{name}: {count} email(s) cleaned")
            )
            if emails:
                self.stdout.write(
                    self.style.SUCCESS(f"Emails: `{('`, `').join(list(emails))}`")
                )
