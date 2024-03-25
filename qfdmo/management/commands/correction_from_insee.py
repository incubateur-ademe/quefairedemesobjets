## DEPRECATED
## Won't be use anymore, Correction as it is known in the project is not used anymore

import datetime
import time
import urllib

from api_insee import ApiInsee
from django.conf import settings
from django.core.management.base import BaseCommand
from django.db.models.functions import Length

from qfdmo.models import (
    ActeurStatus,
    CorrectionActeur,
    CorrectionActeurStatus,
    DisplayedActeur,
)

CLIENT = ApiInsee(key=settings.INSEE_KEY, secret=settings.INSEE_SECRET)

SOURCE = "INSEE"


def refresh_client():
    global CLIENT
    CLIENT = ApiInsee(key=settings.INSEE_KEY, secret=settings.INSEE_SECRET)


def call_api_insee(siren: str) -> dict | None:
    insee_data = None
    if len(siren) != 9:
        return insee_data
    try:
        insee_data = CLIENT.siren(
            siren,
            date=datetime.date.today().strftime("%Y-%m-%d"),
        ).get()
    except urllib.error.HTTPError as e:
        if "404" in str(e):
            return insee_data
        if "403" in str(e):
            print("Forbidden, waiting 60 seconds")
            time.sleep(10)
            refresh_client()
            insee_data = call_api_insee(siren)
        if "429" in str(e):
            print("Too many requests, waiting 1 seconds")
            time.sleep(10)
            insee_data = call_api_insee(siren)
        else:
            raise e
    return insee_data


class Command(BaseCommand):
    help = "Get info from INSEE and save proposition of correction"

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
            DisplayedActeur.objects.annotate(siret_length=Length("siret"))
            .filter(siret_length=14, statut=ActeurStatus.ACTIF)
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
            print(final_acteur, " : ", final_acteur.siret)
            insee_data = call_api_insee(final_acteur.siret[:9])
            if (
                insee_data is not None
                and "uniteLegale" in insee_data
                and "periodesUniteLegale" in insee_data["uniteLegale"]
                and len(insee_data["uniteLegale"]["periodesUniteLegale"]) > 0
            ):
                nom_officiel = insee_data["uniteLegale"]["periodesUniteLegale"][0][
                    "denominationUniteLegale"
                ]
                naf_principal = insee_data["uniteLegale"]["periodesUniteLegale"][0][
                    "activitePrincipaleUniteLegale"
                ]
                siren = insee_data["uniteLegale"]["siren"]
                siret = (
                    siren
                    + insee_data["uniteLegale"]["periodesUniteLegale"][0][
                        "nicSiegeUniteLegale"
                    ]
                )

                changed = False
                acteurfields_to_update = {}
                if nom_officiel != final_acteur.nom_officiel:
                    acteurfields_to_update["nom_officiel"] = nom_officiel
                    changed = True
                if naf_principal != final_acteur.naf_principal:
                    acteurfields_to_update["naf_principal"] = naf_principal
                    changed = True
                if siret != final_acteur.siret:
                    acteurfields_to_update["siret"] = siret
                    changed = True
                CorrectionActeur.objects.create(
                    **acteurfields_to_update,
                    source=SOURCE,
                    resultat_brute_source=insee_data,
                    identifiant_unique=final_acteur.identifiant_unique,
                    final_acteur_id=final_acteur.identifiant_unique,
                    correction_statut=(
                        CorrectionActeurStatus.ACTIF
                        if changed
                        else CorrectionActeurStatus.PAS_DE_MODIF
                    ),
                )
            else:
                CorrectionActeur.objects.create(
                    source=SOURCE,
                    resultat_brute_source="{}",
                    identifiant_unique=final_acteur.identifiant_unique,
                    final_acteur_id=final_acteur.identifiant_unique,
                    correction_statut=CorrectionActeurStatus.ACTIF,
                )
