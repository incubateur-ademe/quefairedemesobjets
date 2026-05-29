import argparse

from data.models.suggestion import SuggestionStatut, SuggestionUnitaire
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Fix not well encoded proposition service codes - should be run only once"

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            help="Run command without writing changes to the database",
            action=argparse.BooleanOptionalAction,
            default=False,
        )

    def handle(self, *args, **options):
        dry_run = options["dry_run"]

        su = SuggestionUnitaire.objects.filter(
            champs=["proposition_service_codes"],
            suggestion_groupe__statut__in=[
                SuggestionStatut.ERREUR,
                SuggestionStatut.AVALIDER,
            ],
        )

        for u in su:
            valeurs = u.valeurs
            psc = valeurs[0]
            if "\"['" in psc and "']\"" in psc:
                npsc = psc.replace("\"['", '["').replace("']\"", '"]')
                self.stdout.write(self.style.SUCCESS(f"psc: {psc} -> {npsc}"))
                if not dry_run:
                    u.valeurs = [npsc]
                    u.save()

        return
