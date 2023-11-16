import datetime

import requests
from django.core.management.base import BaseCommand
from django.db.models import Exists, OuterRef
from django.db.models.functions import Length

from qfdmo.models import (
    ActeurStatus,
    CorrectionActeur,
    CorrectionActeurStatus,
    FinalActeur,
)

SOURCE = "RechercheSiret"


def call_api_recherche_entreprise(entreprise_id: str) -> dict:
    analyse = {
        "siret_exist": True,
        "error": None,
        "etablissement_actif": True,
        "entreprise_active": True,
        "nb_etablissements": None,
        "raw_result": None,
    }
    if len(entreprise_id) == 14:
        response = requests.get(
            "https://api.recherche-entreprises.fabrique.social.gouv.fr/api/v1/"
            f"etablissement/{entreprise_id}"
        )

        if response.status_code == 404:
            analyse["exists"] = False
        elif response.status_code != 200:
            analyse["error"] = {
                "code": response.status_code,
                "message": f"{entreprise_id} - erreur API : {response.text}",
            }
        else:
            etablissement = response.json()

            analyse["etablissement_actif"] = (
                "etatAdministratifEtablissement" in etablissement
                and etablissement["etatAdministratifEtablissement"] == "A"
            )
            analyse["entreprise_active"] = (
                "etatAdministratifUniteLegale" in etablissement
                and etablissement["etatAdministratifUniteLegale"] == "A"
            )
            analyse["nb_etablissements"] = (
                etablissement["etablissements"]
                if "etablissements" in etablissement
                else None
            )
            analyse["raw_result"] = response.json()
        return analyse
    else:
        raise Exception(
            f"should be called with a siret (14 digits), not : {entreprise_id}"
        )


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

        correction_subquery = CorrectionActeur.objects.filter(
            final_acteur_id=OuterRef("identifiant_unique"),
            source=SOURCE,
            cree_le__gte=datetime.datetime.now() - datetime.timedelta(days=31),
        )

        final_acteurs = (
            FinalActeur.objects.annotate(
                siret_length=Length("siret"), has_correction=Exists(correction_subquery)
            )
            .filter(siret_length=14, statut=ActeurStatus.ACTIF, has_correction=False)
            .order_by("?")
        )

        if nb_acteur_limit is not None:
            final_acteurs = final_acteurs[:nb_acteur_limit]

        for final_acteur in final_acteurs:
            print(final_acteur, " : ", final_acteur.siret)
            siret_analyse = call_api_recherche_entreprise(final_acteur.siret)
            if not siret_analyse["siret_exist"]:
                CorrectionActeur.objects.create(
                    source=SOURCE,
                    resultat_brute_source={"code": 404, "message": "Siret non trouvé"},
                    identifiant_unique=final_acteur.identifiant_unique,
                    final_acteur_id=final_acteur.identifiant_unique,
                    correction_statut=CorrectionActeurStatus.ACTIF,
                )
                continue
            if siret_analyse["error"] is not None:
                CorrectionActeur.objects.create(
                    source=SOURCE,
                    resultat_brute_source=siret_analyse["error"],
                    identifiant_unique=final_acteur.identifiant_unique,
                    final_acteur_id=final_acteur.identifiant_unique,
                    correction_statut=CorrectionActeurStatus.ACTIF,
                )
                continue
            if (
                siret_analyse["etablissement_actif"]
                and siret_analyse["entreprise_active"]
            ):
                CorrectionActeur.objects.create(
                    source=SOURCE,
                    resultat_brute_source=siret_analyse,
                    identifiant_unique=final_acteur.identifiant_unique,
                    final_acteur_id=final_acteur.identifiant_unique,
                    correction_statut=CorrectionActeurStatus.PAS_DE_MODIF,
                )
            else:
                CorrectionActeur.objects.create(
                    source=SOURCE,
                    resultat_brute_source=siret_analyse,
                    identifiant_unique=final_acteur.identifiant_unique,
                    final_acteur_id=final_acteur.identifiant_unique,
                    correction_statut=CorrectionActeurStatus.ACTIF,
                )
