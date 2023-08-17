from django.core.management.base import BaseCommand
from django.db import transaction

from qfdmo.models import ActeurService

activities = [
    [163, "Achat, revente entre particuliers"],
    [162, "Achat, revente par un professionnel"],
    [157, "Atelier d'auto-réparation"],
    [164, "Collecte par une structure spécialisée"],
    [161, "Depôt-vente"],
    [165, "Don entre particuliers"],
    [188, "Echanges entre particuliers"],
    [168, "Hub de partage"],
    [167, "Location entre particuliers"],
    [166, "Location par un professionnel"],
    [169, "Partage entre particuliers"],
    [158, "Pièces détachées"],
    [170, "Relai d'acteurs et d'événements"],
    [160, "Ressourcerie, recyclerie"],
    [156, "Service de réparation"],
    [159, "Tutoriels et diagnostics en ligne"],
]


class Command(BaseCommand):
    # pylint: disable=R0912,R0914,R0915
    def handle(self, *args, **options):
        with transaction.atomic():
            ActeurService.objects.all().delete()
            for activity in activities:
                ActeurService.objects.get_or_create(
                    nom=activity[1],
                    lvao_id=activity[0],
                )
