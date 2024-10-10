from datetime import datetime

from django.core.management.base import BaseCommand

from qfdmo.admin import OpenSourceDisplayedActeurResource


class Command(BaseCommand):
    help = "Export Ressources using CSV format"

    def handle(self, *args, **options):
        print(f"Starting : {datetime.now()}")
        dataset = OpenSourceDisplayedActeurResource(
            nb_object=100,
            offset_object=100,
        ).export()

        open("export.xlsx", "w").write(dataset.xlsx)
        print(f"Ended : {datetime.now()}")
        # print(dataset.headers)
        # for row in dataset:
        #     print(row)
