from django.core.management.base import BaseCommand
from django.db import transaction

from qfdmo.models import ActeurService, Action

actions_services = [
    ["acheter d'occasion", "Achat, revente entre particuliers"],
    ["acheter d'occasion", "Achat, revente par un professionnel"],
    ["acheter d'occasion", "Depôt-vente"],
    ["acheter d'occasion", "Relai d'acteurs et d'événements"],
    ["acheter d'occasion", "Ressourcerie, recyclerie"],
    ["donner", "Collecte par une structure spécialisée"],
    ["donner", "Don entre particuliers"],
    ["donner", "Relai d'acteurs et d'événements"],
    ["emprunter", "Hub de partage"],
    ["emprunter", "Partage entre particuliers"],
    ["emprunter", "Relai d'acteurs et d'événements"],
    ["louer", "Location entre particuliers"],
    ["louer", "Location par un professionnel"],
    ["louer", "Relai d'acteurs et d'événements"],
    ["mettre en location", "Location entre particuliers"],
    ["mettre en location", "Location par un professionnel"],
    ["mettre en location", "Relai d'acteurs et d'événements"],
    ["prêter", "Hub de partage"],
    ["prêter", "Partage entre particuliers"],
    ["prêter", "Relai d'acteurs et d'événements"],
    ["revendre", "Achat, revente entre particuliers"],
    ["revendre", "Achat, revente par un professionnel"],
    ["revendre", "Depôt-vente"],
    ["revendre", "Relai d'acteurs et d'événements"],
    ["réparer", "Atelier d'auto-réparation"],
    ["réparer", "Pièces détachées"],
    ["réparer", "Relai d'acteurs et d'événements"],
    ["réparer", "Service de réparation"],
    ["réparer", "Tutoriels et diagnostics en ligne"],
    ["échanger", "Echanges entre particuliers"],
    ["échanger", "Hub de partage"],
    ["échanger", "Relai d'acteurs et d'événements"],
]


class Command(BaseCommand):
    # pylint: disable=R0912,R0914,R0915
    def handle(self, *args, **options):
        with transaction.atomic():
            for action_service in actions_services:
                ActeurService.objects.get(nom=action_service[1]).actions.add(
                    Action.objects.get(nom=action_service[0])
                )
