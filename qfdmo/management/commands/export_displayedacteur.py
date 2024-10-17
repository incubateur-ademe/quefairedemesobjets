from datetime import datetime
from pathlib import Path

import openpyxl
from django.core.management.base import BaseCommand

from qfdmo.admin import OpenSourceDisplayedActeurResource

TARGET_FILE = "export_lavo_acteurs.xlsx"
CHUNK = 1000


class Command(BaseCommand):
    help = "Export Ressources using CSV format"

    def handle(self, *args, **options):
        self.stdout.write(f"Exporting Ressources, starting at {datetime.now()}")

        if Path(TARGET_FILE).exists():
            Path(TARGET_FILE).unlink()

        try:
            workbook = openpyxl.load_workbook(TARGET_FILE)
            sheet = workbook.active
        except FileNotFoundError:
            workbook = openpyxl.Workbook()
            sheet = workbook.active

        offset = 0
        dataset = OpenSourceDisplayedActeurResource(
            nb_objet=CHUNK, offset=offset
        ).export()
        sheet.append(dataset.headers)

        while dataset.dict:
            self.stdout.write(f"Exporting {offset} to {offset + CHUNK}")
            dataset.headers = None

            for row in dataset.dict:
                sheet.append(row)

            offset += CHUNK
            dataset = OpenSourceDisplayedActeurResource(
                nb_objet=CHUNK, offset=offset
            ).export()

        workbook.save(TARGET_FILE)

        self.stdout.write(f"Ended at {datetime.now()}")
