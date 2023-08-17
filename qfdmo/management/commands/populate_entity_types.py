from django.core.management.base import BaseCommand
from django.db import transaction

from qfdmo.models import ActeurType as EntityType

entity_types = [
    [151, "Association, entreprise de l'économie sociale et solidaire"],
    [152, "Collectivité, établissement public"],
    [153, "Artisan, commerce indépendant"],
    [154, "Franchise, enseigne commerciale"],
    [155, "Acteur digital (site web, app. mobile)"],
]


class Command(BaseCommand):
    # pylint: disable=R0912,R0914,R0915
    def handle(self, *args, **options):
        with transaction.atomic():
            EntityType.objects.all().delete()
            for entity_type in entity_types:
                EntityType.objects.get_or_create(
                    nom=entity_type[1],
                    lvao_id=entity_type[0],
                )
