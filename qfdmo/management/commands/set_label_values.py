from django.core.management.base import BaseCommand

from qfdmo.models import LabelQualite


class Command(BaseCommand):
    help = "Closes the specified poll for voting"

    def handle(self, *args, **options):
        LabelQualite.objects.filter(
            code__in=["ess", "reparacteur", "bonusrepar"]
        ).update(filtre=True)

        self.stdout.write(self.style.SUCCESS("Labels mis à jour"))
