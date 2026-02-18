import argparse

from django.core.management.base import BaseCommand
from django.db.models import F

from qfdmo.models.acteur import Acteur, RevisionActeur


class Command(BaseCommand):
    help = "Get info from INSEE and save proposition of correction"

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            help="Run command without writing changes to the database",
            action=argparse.BooleanOptionalAction,
            default=False,
        )

    def handle(self, *args, **options):
        for cls in [Acteur, RevisionActeur]:
            to_update = cls.objects.exclude(description="").filter(
                description=F("consignes_dacces")
            )
            if options["dry_run"]:
                self.stdout.write(
                    self.style.SUCCESS(
                        f"DRY RUN: would update {to_update.count()} {cls.__name__}"
                        " objects"
                    )
                )
            else:
                nb_to_update = to_update.count()
                to_update.update(description="")
                self.stdout.write(
                    self.style.SUCCESS(f"Updated {nb_to_update} {cls.__name__} objects")
                )
