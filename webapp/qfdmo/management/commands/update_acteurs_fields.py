import argparse

import openpyxl
from django.core.management.base import BaseCommand, CommandError
from qfdmo.models.acteur import Acteur, RevisionActeur


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
            help=(
                "Mapping file in xlsx format, first column should be the"
                " identifiant_unique, then next colonne should be the name of the field"
                "to fix (on RevisionActeur)"
            ),
        )

    def revision_acteur_field_names(self) -> set[str]:
        return {
            field.name
            for field in RevisionActeur._meta.get_fields()
            if not field.is_relation
        }

    def validate_headers(self, fields) -> None:
        headers = [field for field in fields if field not in (None, "")]
        if "identifiant_unique" not in headers:
            raise CommandError(
                "The mapping file must contain an `identifiant_unique` column"
            )
        unknown_fields = sorted(
            {
                str(field)
                for field in headers
                if field not in self.revision_acteur_field_names()
            }
        )
        if unknown_fields:
            raise CommandError(
                "Invalid column(s) in mapping file, not RevisionActeur fields: "
                + ", ".join(unknown_fields)
            )

    def read_xlsx_file_to_dict(self, file_path):
        workbook = openpyxl.load_workbook(file_path)
        sheet = workbook.active
        if sheet is None:
            raise ValueError(f"No active sheet found in {file_path}")

        rows = sheet.iter_rows(values_only=True)
        try:
            fields = next(rows)
        except StopIteration as error:
            raise CommandError(f"Mapping file `{file_path}` is empty") from error

        self.validate_headers(fields)
        identifiant_index = list(fields).index("identifiant_unique")
        result = []
        for row in rows:
            identifiant = (
                row[identifiant_index] if identifiant_index < len(row) else None
            )
            if identifiant is None or (
                isinstance(identifiant, str) and not identifiant.strip()
            ):
                break
            result.append(
                {
                    field: value
                    for field, value in zip(fields, row)
                    if field not in (None, "")
                }
            )
        return result

    def values_differ(self, current, new) -> bool:
        if current == new:
            return False
        if current in (None, "") and new in (None, ""):
            return False
        return True

    def has_field_changes(self, instance, updates: dict) -> bool:
        return any(
            self.values_differ(getattr(instance, field), value)
            for field, value in updates.items()
        )

    def handle(self, *args, **options):
        dry_run = options["dry_run"]
        mapping_file = options["mapping_file"]

        mapping = self.read_xlsx_file_to_dict(mapping_file)

        count_updated = 0
        for row in mapping:
            identifiant_unique = row.pop("identifiant_unique")
            revision_acteur = RevisionActeur.objects.filter(
                identifiant_unique=identifiant_unique
            ).first()
            acteur = None
            if not revision_acteur:
                acteur = Acteur.objects.filter(
                    identifiant_unique=identifiant_unique
                ).first()
                if not acteur:
                    self.stdout.write(
                        self.style.WARNING(
                            f"Acteur & RevisionActeur {identifiant_unique} not found"
                        )
                    )
                    continue
                if not self.has_field_changes(acteur, row):
                    self.stdout.write(
                        self.style.WARNING(
                            f"Skipping {identifiant_unique}: no field changes"
                        )
                    )
                    continue

            count_updated += 1
            self.stdout.write(
                self.style.SUCCESS(
                    ("[DRY RUN] " if dry_run else "")
                    + f"{count_updated} / {len(mapping)}: Would update revision acteur "
                    + f"{identifiant_unique} with {row}"
                )
            )
            if dry_run:
                continue
            if not revision_acteur:
                assert acteur is not None
                revision_acteur = acteur.get_or_create_revision()
            for field, value in row.items():
                setattr(revision_acteur, field, value)
            revision_acteur.save()
