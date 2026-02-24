from django.core.management.base import BaseCommand
from django.db.models import F, Value
from django.db.models.functions import Concat, Length

from qfdmo.models.acteur import Acteur, DisplayedActeur, RevisionActeur


class Command(BaseCommand):
    help = "Export Ressources using CSV format"

    def handle(self, *args, **options):
        for cls in [Acteur, RevisionActeur, DisplayedActeur]:
            cls.objects.annotate(len_tel=Length("telephone")).filter(
                len_tel=9, code_postal__lt=96000
            ).update(telephone=Concat(Value("0"), F("telephone")))
