## DEPRECATED
## Won't be use anymore

from django.core.management.base import BaseCommand

from qfdmo.models import Acteur, ActeurStatus, CorrectionActeur, CorrectionActeurStatus


class Command(BaseCommand):
    help = """
Browse acteur correction and remov the acteur which doesn't have activity anymore
"""

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

        corrections = CorrectionActeur.objects.filter(
            correction_statut=CorrectionActeurStatus.ACTIF,
            source="RechercheSiret",
            final_acteur__statut=ActeurStatus.ACTIF,
        )
        if nb_acteur_limit is not None:
            corrections = corrections[:nb_acteur_limit]

        for correction in corrections:
            if (
                correction.resultat_brute_source["entreprise_active"] is False
                and correction.resultat_brute_source["etablissement_actif"] is False
            ) or (
                correction.resultat_brute_source["etablissement_actif"] is False
                and correction.resultat_brute_source["nb_etablissements"] == 1
            ):
                print(f"inactive {correction.identifiant_unique}")
                acteur = Acteur.objects.get(
                    identifiant_unique=correction.identifiant_unique
                )
                revision_acteur = acteur.get_or_create_correctionequipe()
                revision_acteur.statut = ActeurStatus.INACTIF
                revision_acteur.save()
                correction.correction_statut = CorrectionActeurStatus.ACCEPTE
                correction.save()
