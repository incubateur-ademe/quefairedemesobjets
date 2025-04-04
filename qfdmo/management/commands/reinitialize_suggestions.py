from django.core.management.base import BaseCommand
from django.db import connection


class Command(BaseCommand):
    help = "Truncate Suggestions tables and reset auto-increment"

    def handle(self, *args, **options):
        with connection.cursor() as cursor:
            # Truncate the table data_suggestioncohorte and data_suggestion_id_seq
            cursor.execute("TRUNCATE TABLE data_suggestioncohorte CASCADE")

            # Set auto-increment to 1
            cursor.execute(
                "ALTER SEQUENCE data_suggestioncohorte_id_seq RESTART WITH 1"
            )
            cursor.execute("ALTER SEQUENCE data_suggestion_id_seq RESTART WITH 1")
