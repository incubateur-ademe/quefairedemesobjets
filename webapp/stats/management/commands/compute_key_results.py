from django.core.management.base import BaseCommand

from stats.key_results import compute_all


class Command(BaseCommand):
    help = "Calcule les key results et enregistre leurs valeurs"

    def handle(self, *args, **options):
        self.stdout.write(f"{compute_all()} valeurs mises à jour")
