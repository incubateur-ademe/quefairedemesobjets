import tempfile
from datetime import datetime
from pathlib import Path

import openpyxl
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.core.management.base import BaseCommand

from qfdmo.admin import OpenSourceDisplayedActeurResource
from qfdmo.models.acteur import DataLicense

CHUNK = 1000


class Command(BaseCommand):
    help = "Export Ressources using CSV format"

    def add_arguments(self, parser):
        parser.add_argument(
            "--file",
            type=str,
            help="File to export to",
            default=(f"export_acteur_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"),
        )
        parser.add_argument(
            "--licenses",
            nargs="+",
            action="extend",
            type=str,
            help=(
                f"Licenses to export, options : {DataLicense.values}, "
                f"default: '{DataLicense.OPEN_LICENSE.value}'"
            ),
        )

    def handle(self, *args, **options):
        self.stdout.write(
            self.style.SUCCESS(f"Exporting Ressources, starting at {datetime.now()}")
        )
        target_file = "exports/" + options["file"]
        licenses = options["licenses"]
        if not licenses:
            licenses = [DataLicense.OPEN_LICENSE.value]
        if not all(license in DataLicense.values for license in licenses):
            self.stdout.write(
                self.style.ERROR(
                    f"Invalid licenses, options : {licenses}, "
                    f"Available values: '{DataLicense.values}'"
                )
            )
            return

        self.stdout.write(
            self.style.SUCCESS(f"Exporting DisplayedActeur using licenses: {licenses}")
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
                limit=CHUNK, offset=offset, licenses=licenses
            ).export()
            sheet.append(dataset.headers)

            while dataset.dict:
                self.stdout.write(
                    self.style.SUCCESS(f"Exporting {offset} to {offset + CHUNK}")
                )
                dataset.headers = None

                for row in dataset.dict:
                    sheet.append(row)

                offset += CHUNK
                dataset = OpenSourceDisplayedActeurResource(
                    limit=CHUNK, offset=offset, licenses=licenses
                ).export()
            self.stdout.write(self.style.SUCCESS(f"Writing to {target_file}"))

            workbook.save(tmp_file.name)
            tmp_file.seek(0)
            default_storage.save(target_file, ContentFile(tmp_file.read()))

        self.stdout.write(self.style.SUCCESS(f"Ended at {datetime.now()}"))
