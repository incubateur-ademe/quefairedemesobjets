from datetime import datetime

from django.core.management.base import BaseCommand

from qfdmo.admin import OpenSourceDisplayedActeurResource


class Command(BaseCommand):
    help = "Export Ressources using CSV format"

    def handle(self, *args, **options):
        # Méthode brute force
        # TODO: faire cette export de manière itérative par chunk de 1000 par exemple
        self.stdout.write(f"Exporting Ressources, starting at {datetime.now()}")

        dataset = OpenSourceDisplayedActeurResource().export()
        with open("export.xlsx", "wb") as f:
            f.write(dataset.xlsx)

        self.stdout.write(f"Ended at {datetime.now()}")
