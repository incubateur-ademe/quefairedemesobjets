import datetime
import http
import time
import urllib

from api_insee import ApiInsee
from django.conf import settings
from django.core.management.base import BaseCommand
from django.db.models.functions import Length

from qfdmo.models import (
    Acteur,
    CorrecteurActeurStatus,
    CorrectionActeur,
    FinalActeur,
    RevisionActeur,
)

client = ApiInsee(key=settings.INSEE_KEY, secret=settings.INSEE_SECRET)

SOURCE = "INSEE"


def call_api_insee(siren: str) -> dict | None:
    insee_data = None
    if len(siren) != 9:
        return insee_data
    try:
        insee_data = client.siren(
            siren,
            date=datetime.date.today().strftime("%Y-%m-%d"),
        ).get()
    except urllib.error.HTTPError | http.client.RemoteDisconnected as e:
        if "404" in str(e):
            pass
        if "429" in str(e):
            print("Too many requests, waiting 3 seconds")
            time.sleep(3)
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
            FinalActeur.objects.annotate(siret_length=Length("siret"))
            .filter(siret_length=14)
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
                acteurfields_to_update = {
                    "nom_officiel": nom_officiel,
                    "naf_principal": naf_principal,
                    "siret": siret,
                }
                _update_acteur(
                    final_acteur.identifiant_unique,
                    acteurfields_to_update,
                )

                CorrectionActeur.objects.create(
                    **acteurfields_to_update,
                    source=SOURCE,
                    resultat_brute_source=insee_data,
                    identifiant_unique=final_acteur.identifiant_unique,
                    final_acteur_id=final_acteur.identifiant_unique,
                    correction_statut=CorrecteurActeurStatus.NOT_CHANGED,
                )
            else:
                CorrectionActeur.objects.create(
                    source=SOURCE,
                    siret=None,
                    resultat_brute_source="{}",
                    identifiant_unique=final_acteur.identifiant_unique,
                    final_acteur_id=final_acteur.identifiant_unique,
                )


def _update_acteur(identifiant_unique: str, actorfields_to_update: dict):
    acteur = Acteur.objects.get(identifiant_unique=identifiant_unique)
    for field, value in actorfields_to_update.items():
        setattr(acteur, field, value)
    acteur.save()
    RevisionActeur.objects.filter(identifiant_unique=identifiant_unique).update(
        **{field: None for field, _ in actorfields_to_update.items()}
    )
