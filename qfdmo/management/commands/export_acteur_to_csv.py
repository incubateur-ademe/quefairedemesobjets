## DEPRECATED
## Won't be used anymore

import csv

from django.core.management.base import BaseCommand

from qfdmo.models import ActeurStatus, DisplayedActeur
from qfdmo.serializer import DisplayedActeurSerializer


class Command(BaseCommand):
    help = "Export Ressources using CSV format"

    def add_arguments(self, parser):
        parser.add_argument(
            "--limit",
            help="limit the number of acteurs to process",
            type=int,
            default=None,
        )

    def handle(self, *args, **options):
        nb_acteur_limit = options.get("limit")
        results = []
        displayed_acteurs = (
            DisplayedActeur.objects.exclude(source__nom="CartEco - ESS France")
            .exclude(source__nom="CMA - Chambre des métiers et de l'artisanat")
            .exclude(source__nom="REFASHION")
            .filter(statut=ActeurStatus.ACTIF)
            .prefetch_related(
                "proposition_services__sous_categories",
                "proposition_services__acteur_service",
                "acteur_type",
            )
            .order_by("?")
        )
        if nb_acteur_limit is not None:
            displayed_acteurs = displayed_acteurs[:nb_acteur_limit]
        results = DisplayedActeurSerializer(displayed_acteurs, many=True).data

        with open("output.csv", "w", newline="") as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(results[0].keys())  # Write header row
            for result in results:
                writer.writerow(result.values())  # Write data rows
