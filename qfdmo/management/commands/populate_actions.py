from django.core.management.base import BaseCommand
from django.db import transaction

from qfdmo.models import Action

actions = [
    [9, "réparer"],
    [44, "acheter d'occasion"],
    [6, "revendre"],
    [7, "donner"],
    [4, "louer"],
    [50, "mettre en location"],
    [51, "emprunter"],
    [5, "prêter"],
    [8, "échanger"],
]


class Command(BaseCommand):
    # pylint: disable=R0912,R0914,R0915
    def handle(self, *args, **options):
        with transaction.atomic():
            Action.objects.all().delete()
            for action in actions:
                Action.objects.get_or_create(
                    nom=action[1],
                    lvao_id=action[0],
                )
