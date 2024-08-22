# A partir du fichier : https://docs.google.com/spreadsheets/d/1WIKCP3mye_ZYWVAyKecwHN5xrwaU0EUp/edit?usp=sharing&ouid=114461779294398717478&rtpof=true&sd=true

# si il existe déjà un objet avec le nom, on met à jour l'identifiant_qfdmod
# on crée les synomimes si ils n'existent pas

# 1 match des sous-categories de la colonne P
# si pas de colonne P, on crée catégorie colonne B et sous-catégorie de la colonne M


from functools import reduce
from operator import or_
from typing import List

import requests
from django.core.management.base import BaseCommand
from django.db.models import Q

from qfdmo.models.categorie_objet import Objet

produits_qfdmod_url = (
    "https://data.ademe.fr/data-fair/api/v1/datasets/que-faire-de-mes-dechets-produits"
    "/lines?size=10000"
)


def _get_qfdmod_products():
    # Download product in json format from URL
    response = requests.get(produits_qfdmod_url)
    response.raise_for_status()

    return response.json()["results"]


def _get_product_names_from_qfdmod_product(qfdmod_product: dict) -> List[str]:
    product_names = [
        word.lower().strip()
        for word in qfdmod_product["Synonymes_existants"].split("/")
        if word.lower().strip()
    ]
    product_names.append(qfdmod_product["Nom"].lower().strip())
    product_names = list(set(product_names))
    return product_names


def _choose_sous_categorie(sous_categories, product_name):
    chosen_sous_categorie = None
    while chosen_sous_categorie is None:
        sous_categorie_options = "\n".join(
            [
                f"{i + 1} : {prop.libelle} ({prop.categorie.libelle})"
                for i, prop in enumerate(sous_categories)
            ]
        )

        input_text = f"""
Pour le produit : {product_name}
Choisissez la categorie adéquat ?

{sous_categorie_options}
0 : Ignorer

Votre choix : """
        chosen_sous_categorie = input(input_text)
        if not chosen_sous_categorie.isnumeric() or int(
            chosen_sous_categorie
        ) not in range(0, len(sous_categories) + 1):
            chosen_sous_categorie = None
    if chosen_sous_categorie == "0":
        return None
    return sous_categories[int(chosen_sous_categorie) - 1]


def _create_or_update_object_from_product(
    product_id, product_names, sous_categories, result_in_details
):
    """
    If one category found,
    Create unknow product using this categories
    Update identifiant_qfdmod if product already exist
    If more than one, ask user to choose the right one
    """
    for product_name in product_names:
        obj = Objet.objects.filter(
            Q(libelle__iexact=product_name) | Q(code__iexact=product_name)
        ).first()
        if obj:
            if obj.identifiant_qfdmod and obj.identifiant_qfdmod != product_id:
                result_in_details["multi_assignments"].append(product_name)
            obj.identifiant_qfdmod = product_id
            obj.save()
        else:
            # choose categories
            if len(sous_categories) > 1:
                sous_categorie = _choose_sous_categorie(sous_categories, product_name)
                if sous_categorie is None:
                    continue
            else:
                sous_categorie = sous_categories[0]
            Objet.objects.create(
                libelle=product_name,
                code=product_name,
                identifiant_qfdmod=product_id,
                sous_categorie=sous_categorie,
            )
    return result_in_details


def _should_create_products(
    qfdmod_product, objects_from_names, product_names, sous_categories
):
    product_name = qfdmod_product["Nom"]
    collect_names_from_objects = [
        objet.libelle.lower().strip() for objet in objects_from_names
    ] + [objet.code.lower().strip() for objet in objects_from_names]

    if len(sous_categories) == 1 and len(product_names) != len(objects_from_names):
        sous_categorie_libelle = sous_categories[0].libelle
        categorie_libelle = sous_categories[0].categorie.libelle
        inpuut_text = f"""
Pour le produit « {product_name} »
Avec la sous categorie {sous_categorie_libelle} ({categorie_libelle})
Les produits trouvés sont : {' / '.join([
    product_name
    for product_name in product_names
    if product_name in collect_names_from_objects
])}
Les produits suivants seront créés : {' / '.join([
    product_name
    for product_name in product_names
    if product_name not in collect_names_from_objects
])}
Voulez-vous créer ces objets ? (y/n) : """
        should_create = None
        while should_create not in ["y", "n"]:
            should_create = input(inpuut_text).lower()
        return should_create == "y"
    return True


class Command(BaseCommand):
    help = "Get info from INSEE and save proposition of correction"

    def handle(self, *args, **options):
        qfdmod_products = _get_qfdmod_products()

        result_in_details = {
            "multi_assignments": [],
            "count_product_with_multi_catgories": 0,
            "count_product_found_in_object_list": 0,
            "count_product_not_found_in_object_list": 0,
            "count_qfdmod_products": len(qfdmod_products),
        }

        # si il existe déjà un objet avec le nom, on met à jour l'identifiant_qfdmod
        # on crée les synomimes si ils n'existent pas
        for qfdmod_product in qfdmod_products:
            product_id = int(qfdmod_product["ID"])
            product_names = _get_product_names_from_qfdmod_product(qfdmod_product)

            # Construire une liste de filtres Q pour chaque nom de produit
            q_objects_libelle = [Q(libelle__iexact=name) for name in product_names]
            q_objects_code = [Q(code__iexact=name) for name in product_names]
            q_objects = q_objects_libelle + q_objects_code

            # Combiner les filtres Q avec reduce et operator.or_
            objects_from_names = Objet.objects.prefetch_related(
                "sous_categorie"
            ).filter(reduce(or_, q_objects))

            if objects_from_names.count():
                result_in_details["count_product_found_in_object_list"] += 1

                # Collect sous categories from objects

                sous_categories = [objet.sous_categorie for objet in objects_from_names]
                sous_categories = list(set(sous_categories))

                # Raise if no categories found (should never append)
                if len(sous_categories) == 0:
                    raise Exception(
                        f"Pas de sous catégories pour {product_names} "
                        f"{objects_from_names}"
                    )

                if not _should_create_products(
                    qfdmod_product, objects_from_names, product_names, sous_categories
                ):
                    continue

                result_in_details = _create_or_update_object_from_product(
                    product_id,
                    product_names,
                    sous_categories,
                    result_in_details,
                )

            else:
                result_in_details["count_product_not_found_in_object_list"] += 1
        print(result_in_details)
