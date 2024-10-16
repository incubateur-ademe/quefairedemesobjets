from datetime import datetime

from django.core.management.base import BaseCommand

from qfdmo.admin import OpenSourceDisplayedActeurResource


class Command(BaseCommand):
    help = "Export Ressources using CSV format"

    def handle(self, *args, **options):
        print(f"Starting : {datetime.now()}")

        # Exporter les données dans un fichier CSV
        # par chunk de 1000 lignes
        dataset = OpenSourceDisplayedActeurResource().export()

        # open("export.csv", "w").write(dataset.csv)

        # Écrire les données dans un fichier XLSX
        with open("export.xlsx", "wb") as f:
            f.write(dataset.xlsx)

        print(f"Ended : {datetime.now()}")
        # print(dataset.headers)
        # for row in dataset:
        #     print(row)
