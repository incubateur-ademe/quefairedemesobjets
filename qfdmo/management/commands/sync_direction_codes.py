from django.core.management.base import BaseCommand

from qfdmo.models.action import Action
from qfdmo.models.config import CarteConfig


class Command(BaseCommand):
    help = """
    Mise à jour des directions_codes (qui remplacent directions) pour les objets
    Action et CarteConfig
    """

    def handle(self, *args, **kwargs):
        for action in Action.objects.prefetch_related("directions"):
            action.direction_codes = [
                direction.code for direction in action.directions.all()
            ]
            action.save()
        for carte in CarteConfig.objects.prefetch_related("direction"):
            carte.direction_codes = [
                direction.code for direction in carte.direction.all()
            ]
            carte.save()
