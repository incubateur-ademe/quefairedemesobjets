import argparse
import logging

from django.core.management.base import BaseCommand
from qfdmo.models.categorie_objet import SousCategorieObjet

logger = logging.getLogger(__name__)

OLD_CODE = "mélange_d_inertes_produits_et_materiaux_de_construction_du_batiment"
NEW_CODE = "melange_d_inertes_produits_et_materiaux_de_construction_du_batiment"


class Command(BaseCommand):
    help = "Rename SousCategorieObjet code to fix accented character"

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            help="Run command without writing changes to the database",
            action=argparse.BooleanOptionalAction,
            default=False,
        )
        parser.add_argument(
            "--old_code",
            help="Code original to rename",
            type=str,
            default=OLD_CODE,
        )
        parser.add_argument(
            "--new_code",
            help="Code new to rename",
            type=str,
            default=NEW_CODE,
        )

    def handle(self, *args, **options):
        dry_run = options["dry_run"]
        old_code = options["old_code"]
        new_code = options["new_code"]

        try:
            sous_categorie = SousCategorieObjet.objects.get(code=old_code)
        except SousCategorieObjet.DoesNotExist:
            self.stdout.write(
                self.style.WARNING(
                    f"SousCategorieObjet with code '{old_code}' not found"
                )
            )
            return

        if SousCategorieObjet.objects.filter(code=new_code).exists():
            self.stdout.write(
                self.style.ERROR(
                    f"SousCategorieObjet with code '{new_code}' already exists"
                )
            )
            return

        if dry_run:
            self.stdout.write(
                self.style.SUCCESS(
                    f"DRY RUN - Would rename code '{old_code}' to '{new_code}'"
                )
            )
        else:
            sous_categorie.code = new_code
            sous_categorie.save(update_fields=["code"])
            self.stdout.write(
                self.style.SUCCESS(f"Renamed code '{old_code}' to '{new_code}'")
            )
