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
from qfdmo.models.acteur import Acteur

SOURCE = "Recherche entreprise"


def call_api_recherche_entreprise(entreprise_id: str) -> dict | None:
    insee_data = None
    if len(entreprise_id) == 14:
        response = requests.get(
            "https://api.recherche-entreprises.fabrique.social.gouv.fr/api/v1/"
            f"etablissement/{entreprise_id}"
        )
        if response.status_code == 404:
            # Should be removed
            return insee_data
        if response.status_code != 200:
            print(f"error {response.status_code} : {entreprise_id}")
        return response.json()

    print(f"not the right length : {entreprise_id}")
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
            insee_data = call_api_recherche_entreprise(final_acteur.siret)

            if insee_data is not None:
                if "activitePrincipaleEtablissement" in insee_data:
                    acteur = Acteur.objects.get(
                        identifiant_unique=final_acteur.identifiant_unique
                    )
                    acteur.naf_principal = insee_data["activitePrincipaleEtablissement"]
                    acteur.save()

                CorrectionActeur.objects.create(
                    source=SOURCE,
                    resultat_brute_source=insee_data,
                    identifiant_unique=final_acteur.identifiant_unique,
                    final_acteur_id=final_acteur.identifiant_unique,
                    correction_statut=CorrectionActeurStatus.PAS_DE_MODIF,
                )
            else:
                CorrectionActeur.objects.create(
                    source=SOURCE,
                    resultat_brute_source="{}",
                    identifiant_unique=final_acteur.identifiant_unique,
                    final_acteur_id=final_acteur.identifiant_unique,
                    correction_statut=CorrectionActeurStatus.ACTIF,
                )
