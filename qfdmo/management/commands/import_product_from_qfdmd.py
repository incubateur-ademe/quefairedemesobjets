## DEPRECATED
## Won't be use anymore, Correction as it is known in the project is not used anymore

import csv

import jellyfish
from django.core.management.base import BaseCommand

from qfdmo.models.categorie_objet import Objet

csv_filepath = "que-faire-de-mes-dechets-produits.csv"

test = {
    "Nom": "…",
    "Synonymes_existants": "…",
    "Code": "…",
    "Bdd": "…",
    "Comment_les_eviter_?": "…",
    "Qu'est-@ce_que_j'en_fais_?": "…",
    "Que_va-t-@il_devenir_?": "…",
    "nom_eco_organisme": "…",
    "filieres_REP": "…",
}


class Command(BaseCommand):
    help = "Get info from INSEE and save proposition of correction"

    def handle(self, *args, **options):

        # ajoute du champ identifiant qfdmod
        # on garde le lien entre le produit et ses synonymes
        # si un des synonymes est connu, on crée tous les synonymes qui appartiennent
        # à la même sous-catégorie

        product_fulllist = []
        # extract product name and synomimes
        with open(csv_filepath, mode="r", encoding="utf-8") as file:
            reader = csv.DictReader(file)
            for row in reader:
                synonymes = [
                    syn.strip()
                    for syn in row["Synonymes_existants"].split("/")
                    if len(syn.strip())
                ]
                for synonyme in synonymes:

                    clone = row.copy()
                    clone["Nom"] = synonyme
                    product_fulllist.append(clone)
                product_fulllist.append(row)

        # objects = {obj.libelle.lower(): obj for obj in Objet.objects.all()}
        object_names = [obj.libelle.lower() for obj in Objet.objects.all()]
        # print(object_names)

        known_objects = []
        unknown_objects = []
        for row in product_fulllist:
            name = row["Nom"].lower()
            if name in object_names:
                known_objects.append(row)
                # exacte match
            else:
                comparison = [
                    (obj_name, jellyfish.jaro_similarity(name, obj_name))
                    for obj_name in object_names
                ]
                # get the 5 best match
                comparison = sorted(comparison, key=lambda item: item[1], reverse=True)[
                    :5
                ]
                print(comparison)
                # sort by value
                # comparison = dict(
                #     sorted(
                #         comparison.items(), key=lambda item: item[1], reverse=True
                #     )
                # )
                print(name)
                #                    print([comparison.keys()][:5])

                unknown_objects.append(row)

        print(" --- ".join([obj["Nom"] for obj in unknown_objects]))
        print(f"{len(known_objects)} known objects")
        print(f"{len(unknown_objects)} unknown objects")
        # quiet = options.get("quiet")
        # nb_acteur_limit = options.get("limit")

    def add_arguments(self, parser):
        pass
        # parser.add_argument(
        #     "--limit",
        #     help="limit the number of acteurs to process",
        #     type=int,
        #     default=None,
        # )
        # parser.add_argument(
        #     "--quiet",
        #     help="limit the number of acteurs to process",
        #     type=bool,
        #     default=False,
        # )
