import requests
from django.core.management.base import BaseCommand

from qfdmo.models import CorrectionActeur, FinalActeur


class Command(BaseCommand):
    help = "Get info from INSEE and save proposition of correction"

    def add_arguments(self, parser):
        parser.add_argument(
            "--limit",
            help="limit the number of acteurs to process",
            type=int,
            default=None,
        )

    def handle(self, *args, **options):
        result = input(
            "Avant de commencer, avez vous bien mis à jour les vues matérialisées ?"
            " (y/N)"
        )
        if result.lower() != "y":
            print(
                "Veuillez mettre à jour les vues matérialisées avant de lancer ce"
                " script"
            )
            return

        nb_acteur_limit = options.get("limit")

        final_acteurs = (
            FinalActeur.objects.exclude(url__isnull=True).exclude(url="").order_by("?")
        )

        if nb_acteur_limit is not None:
            final_acteurs = final_acteurs[:nb_acteur_limit]

        for final_acteur in final_acteurs:
            try:
                response = requests.head(final_acteur.url, timeout=30)
            except:  # noqa: E722
                print(f"Connection error for {final_acteur.url}")
                CorrectionActeur.objects.create(
                    source="URL",
                    url=None,
                    identifiant_unique=final_acteur.identifiant_unique,
                    final_acteur_id=final_acteur.identifiant_unique,
                    resultat_brute_source="{}",
                )
                continue
            if response.status_code >= 400:
                CorrectionActeur.objects.create(
                    source="URL",
                    url=None,
                    identifiant_unique=final_acteur.identifiant_unique,
                    final_acteur_id=final_acteur.identifiant_unique,
                    resultat_brute_source="{}",
                )
            else:
                print(f"Processing {final_acteur.url} : {response.status_code}")
