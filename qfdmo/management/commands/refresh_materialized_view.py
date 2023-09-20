from django.core.management.base import BaseCommand

from qfdmo.models import FinalActeur


class Command(BaseCommand):
    help = "Refresh materialized view"

    def handle(self, *args, **options):
        FinalActeur.refresh_view()
