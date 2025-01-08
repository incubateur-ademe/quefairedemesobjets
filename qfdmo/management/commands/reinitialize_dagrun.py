from django.core.management.base import BaseCommand
from django.db import connection


class Command(BaseCommand):
    help = "Export Ressources using CSV format"

    def handle(self, *args, **options):
        with connection.cursor() as cursor:
            # Truncate the table qfdmo_suggestioncohorte and qfdmo_suggestionunitaire
            cursor.execute("TRUNCATE TABLE qfdmo_suggestioncohorte CASCADE")

            # Set auto-increment to 1
            cursor.execute(
                "ALTER SEQUENCE qfdmo_suggestioncohorte_id_seq RESTART WITH 1"
            )
            cursor.execute(
                "ALTER SEQUENCE qfdmo_suggestionunitaire_id_seq RESTART WITH 1"
            )
