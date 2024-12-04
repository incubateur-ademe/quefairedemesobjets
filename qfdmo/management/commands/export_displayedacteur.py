import tempfile
from datetime import datetime
from pathlib import Path

import openpyxl
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.core.management.base import BaseCommand

from qfdmo.admin import OpenSourceDisplayedActeurResource

CHUNK = 1000


class Command(BaseCommand):
    help = "Export Ressources using CSV format"

    def handle(self, *args, **options):
        self.stdout.write(f"Exporting Ressources, starting at {datetime.now()}")
        target_file = datetime.now().strftime(
            "exports/export_acteur_%Y%m%d_%H%M%S.xlsx"
        )

        with tempfile.NamedTemporaryFile(mode="w+b", suffix=".xlsx") as tmp_file:
            try:
                workbook = openpyxl.load_workbook(Path(tmp_file.name).name)
                sheet = workbook.active
            except FileNotFoundError:
                workbook = openpyxl.Workbook()
                sheet = workbook.active

            offset = 0
            dataset = OpenSourceDisplayedActeurResource(
                limit=CHUNK, offset=offset
            ).export()
            sheet.append(dataset.headers)

            while dataset.dict:
                self.stdout.write(f"Exporting {offset} to {offset + CHUNK}")
                dataset.headers = None

                for row in dataset.dict:
                    sheet.append(row)

                offset += CHUNK
                dataset = OpenSourceDisplayedActeurResource(
                    limit=CHUNK, offset=offset
                ).export()

            self.stdout.write(f"Writing to {target_file}")

            workbook.save(tmp_file.name)
            tmp_file.seek(0)
            default_storage.save(target_file, ContentFile(tmp_file.read()))

        self.stdout.write(f"Ended at {datetime.now()}")
