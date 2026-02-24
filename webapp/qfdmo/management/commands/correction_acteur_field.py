"""
Correction des horaires OSM
"""

import argparse

from django.core.management.base import BaseCommand

from qfdmo.models.acteur import Acteur, RevisionActeur, VueActeur


class Command(BaseCommand):
    help = "Test url availability and save proposition of correction"

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            help="Run command without writing changes to the database",
            action=argparse.BooleanOptionalAction,
            default=False,
        )
        parser.add_argument(
            "--field",
            help="Field to correct",
            type=str,
            required=True,
            # default="horaires_osm",
        )
        parser.add_argument(
            "--old_value",
            help="Old value to filter",
            type=str,
            required=True,
            # default="Mo off; Tu off; We off; Th off; Fr off; Sa off; Su off",
        )
        parser.add_argument(
            "--new_value",
            help="Value to replace",
            type=str,
            required=True,
            # default="__empty__",
        )

    def handle(self, *args, **options):
        dry_run = options.get("dry_run")
        field = options.get("field")
        old_value = options.get("old_value")
        new_value = options.get("new_value")
        count = 0

        filter_kwargs = {f"{field}__icontains": old_value}

        for vueacteur in VueActeur.objects.filter(**filter_kwargs):
            revision = None
            identifiant_unique = vueacteur.identifiant_unique
            try:
                acteur = Acteur.objects.get(identifiant_unique=identifiant_unique)
                revision = acteur.get_or_create_revision()
            except Acteur.DoesNotExist:
                revision = RevisionActeur.objects.get(
                    identifiant_unique=identifiant_unique
                )

            setattr(revision, field, new_value)
            count += 1
            self.stdout.write(
                self.style.SUCCESS(
                    f"{dry_run and 'DRY RUN ' or ''}{identifiant_unique}"
                    f" - update {field}: from {old_value} to {new_value}"
                )
            )
            if not dry_run:
                revision.save()

        print(f"Nb d'acteurs {'à modifier' if dry_run else 'modifiés'}: {count}")
