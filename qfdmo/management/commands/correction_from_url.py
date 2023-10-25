import datetime

import requests
from django.core.management.base import BaseCommand
from django.db.models.functions import Length

from qfdmo.models import CorrecteurActeurStatus, CorrectionActeur, FinalActeur

SOURCE = "URL_SCRIPT"


class Command(BaseCommand):
    help = "Test url availability and save proposition of correction"

    def add_arguments(self, parser):
        parser.add_argument(
            "--limit",
            help="limit the number of acteurs to process",
            type=int,
            default=None,
        )
        parser.add_argument(
            "--quiet",
            help="limit the number of acteurs to process",
            type=bool,
            default=False,
        )

    def handle(self, *args, **options):
        quiet = options.get("quiet")
        nb_acteur_limit = options.get("limit")
        if not quiet:
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

        final_acteurs = (
            FinalActeur.objects.annotate(url_length=Length("url"))
            .filter(url_length__gt=3)
            .exclude(
                identifiant_unique__in=CorrectionActeur.objects.values_list(
                    "identifiant_unique", flat=True
                ).filter(
                    source=SOURCE,
                    cree_le__gte=datetime.datetime.now() - datetime.timedelta(days=31),
                ),
            )
            .order_by("?")
        )

        if nb_acteur_limit is not None:
            final_acteurs = final_acteurs[:nb_acteur_limit]

        for final_acteur in final_acteurs:
            response = None
            failed = False
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
                " AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110"
                " Safari/537.36"
            }
            try:
                response = requests.head(final_acteur.url, timeout=60, headers=headers)
                print(f"Processing {final_acteur.url} : {response.status_code}")
            except requests.exceptions.MissingSchema:
                response = requests.get(final_acteur.url, timeout=60, headers=headers)
                print(f"Processing {final_acteur.url} : {response.status_code}")
            except requests.exceptions.ConnectionError:
                print(f"Connection error for {final_acteur.url}")
            if response is None or response.status_code >= 400:
                failed = True

            CorrectionActeur.objects.create(
                source=SOURCE,
                url=None if failed else final_acteur.url,
                identifiant_unique=final_acteur.identifiant_unique,
                final_acteur_id=final_acteur.identifiant_unique,
                resultat_brute_source="{}",
                correction_statut=CorrecteurActeurStatus.ACTIF
                if failed
                else CorrecteurActeurStatus.NOT_CHANGED,
            )
