import logging

from django.core.management.base import BaseCommand
from django.db import models, transaction

from qfdmo.models import Acteur, DisplayedActeur, RevisionActeur

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Copy acteur services from proposition services to acteurs"

    def handle(self, *args, **options):
        for cls in [Acteur, RevisionActeur, DisplayedActeur]:
            logger.warning(f"Copying acteur services to {cls.__name__}")

            acteur_query = (
                cls.objects.prefetch_related("proposition_services__acteur_service")
                .annotate(count_acteur_services=models.Count("acteur_services"))
                .filter(count_acteur_services=0)
            )
            count = 0
            total = acteur_query.count()
            # collect acteur services from proposition services
            for acteur in acteur_query:
                count += 1
                if count % 1000 == 0:
                    logger.warning(f"Processing {count} {cls.__name__} / {total}")
                # collect acteur services from proposition services

                acteur_services = list(
                    set(
                        [
                            proposition_service.acteur_service
                            for proposition_service in acteur.proposition_services.all()
                            if proposition_service.acteur_service
                        ]
                    )
                )
                with transaction.atomic():
                    acteur.acteur_services.add(*acteur_services)
            logger.warning(f"Processed {count} {cls.__name__}")
