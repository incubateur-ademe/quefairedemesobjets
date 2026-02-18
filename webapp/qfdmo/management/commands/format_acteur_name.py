import re

from django.core.management.base import BaseCommand

from qfdmo.models import Acteur, DisplayedActeur


def formatted_string(string: str) -> str:
    result = string.title().strip().replace("  ", " ")

    if result.upper().startswith("SA "):
        result = "SA " + result[3:]
    if result.upper().startswith("SA."):
        result = "SA." + result[3:]
    if result.upper().endswith(" SA"):
        result = result[:-3] + " SA"

    if result.upper().startswith("SAS "):
        result = "SAS " + result[4:]
    if result.upper().startswith("SAS."):
        result = "SAS." + result[4:]
    if result.upper().endswith(" SAS"):
        result = result[:-4] + " SAS"

    for word in result.split(" "):
        if len(word) >= 3 and re.match("^[^aeiouAEIOU]+$", word):
            result = result.replace(word, word.upper())

    if result.upper().startswith("SARL "):
        result = "SARL " + result[5:]
    if result.upper().endswith(" SARL"):
        result = result[:-5] + " SARL"
    result = result.replace(" Sarl ", " SARL ")

    if result.upper().startswith("ETS "):
        result = "Éts " + result[4:]
    if result.upper().endswith(" ETS"):
        result = result[:-4] + " Éts"
    result = result.replace(" Ets ", " Éts ")

    result = result.replace("Boîte À Lire", "Boîte à lire")
    result = result.replace("D Or", "D'Or")

    # if result.upper().startswith("L "):
    #     result = "L'" + result[2:]
    # result = result.replace(" L ", " L'")

    return result


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

        final_acteurs = DisplayedActeur.objects.all().order_by("?")

        if nb_acteur_limit is not None:
            final_acteurs = final_acteurs[:nb_acteur_limit]
        count = 0
        total = final_acteurs.count()
        for final_acteur in final_acteurs:
            nom = final_acteur.nom
            nom_commercial = final_acteur.nom_commercial

            formatted_nom = formatted_string(nom)
            formatted_nom_commercial = None
            if nom_commercial:
                formatted_nom_commercial = formatted_string(nom_commercial)
            else:
                nom_commercial = None

            if formatted_nom == nom and formatted_nom_commercial == nom_commercial:
                continue

            count += 1
            acteur = Acteur.objects.get(
                identifiant_unique=final_acteur.identifiant_unique
            )
            revision_acteur = acteur.get_or_create_correctionequipe()
            revision_acteur.nom = formatted_nom
            revision_acteur.nom_commercial = formatted_nom_commercial
            revision_acteur.save()
            print(final_acteur, " : ", revision_acteur)
            if count % 100 == 0:
                print("Nb d'acteur modifier: ", count, "/", total)

        print("Nb d'acteur modifier: ", count)
