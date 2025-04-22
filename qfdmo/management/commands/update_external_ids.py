import argparse
import json

from django.core.management.base import BaseCommand

from qfdmo.models.acteur import Acteur, RevisionActeur

CHUNK = 1000


class Command(BaseCommand):
    help = "Export Ressources using CSV format"

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            help="Run command without writing changes to the database",
            action=argparse.BooleanOptionalAction,
            default=False,
        )
        parser.add_argument(
            "--mapping-file",
            type=str,
            required=True,
            help="Mapping file in json format",
        )
        parser.add_argument(
            "--source-code",
            type=str,
            required=True,
            help="Code of the source to update",
        )

    def handle(self, *args, **options):
        dry_run = options["dry_run"]
        mapping_file = options["mapping_file"]
        source_code = options["source_code"]

        with open(mapping_file, "r") as f:
            mapping = json.load(f)

        for old_id, new_id in mapping.items():
            # Check if the ids are not empty
            if old_id and new_id:
                self.stdout.write(
                    self.style.SUCCESS(f"Updating `{old_id}` to `{new_id}`")
                )
            else:
                self.stdout.write(
                    self.style.WARNING(
                        f"Skipping `{old_id}` to `{new_id}` : one of the ids is empty"
                    )
                )
                continue

            # Update acteur if exists
            acteur = Acteur.objects.filter(
                identifiant_externe=old_id, source__code=source_code
            ).first()

            if not acteur:
                self.stdout.write(self.style.WARNING(f"Acteur {old_id} not found"))
                continue

            if not dry_run:
                self.stdout.write(
                    self.style.SUCCESS(
                        f"Updating acteur {acteur.identifiant_unique} to {new_id}"
                    )
                )
                acteur.identifiant_externe = new_id
                acteur.save()
            else:
                self.stdout.write(
                    self.style.WARNING(
                        f"Dry run: would update Acteur {old_id} to {new_id}"
                    )
                )

            # Update revision acteur if exists
            revision_acteur = RevisionActeur.objects.filter(
                identifiant_externe=old_id, source__code=source_code
            ).first()

            if revision_acteur and not dry_run:
                self.stdout.write(
                    self.style.SUCCESS(
                        f"Updating revision acteur {revision_acteur.identifiant_unique}"
                        f" to {new_id}"
                    )
                )
                revision_acteur.identifiant_externe = new_id
                revision_acteur.save()
            if revision_acteur and dry_run:
                self.stdout.write(
                    self.style.WARNING(
                        f"Dry run: would update RevisionActeur {old_id} to {new_id}"
                    )
                )
