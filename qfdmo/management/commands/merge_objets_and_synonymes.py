import argparse
import csv
from pathlib import Path

from django.core.management.base import BaseCommand

from qfdmd.models import Produit, Synonyme
from qfdmo.models.categorie_objet import Objet


class Command(BaseCommand):
    help = "Export Ressources using CSV format"

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            help="Run command without writing changes to the database",
            action=argparse.BooleanOptionalAction,
            default=False,
        )
        parser.add_argument(
            "--output_objets",
            help="Path to output CSV file for objets",
            type=str,
            default="synonymes_a_creer.csv",
        )
        parser.add_argument(
            "--output_conflict",
            help="Path to output CSV file for conflicts",
            type=str,
            default="sous_categories_conflits.csv",
        )
        parser.add_argument(
            "--output_synonymes_sans_objets",
            help="Path to output CSV file for synonymes sans objets",
            type=str,
            default="synonymes_sans_objets.csv",
        )

    def handle(self, *args, **options):
        dry_run = options["dry_run"]
        output_objets_file = options["output_objets"]
        output_conflict_file = options["output_conflict"]
        output_synonymes_sans_objets_file = options["output_synonymes_sans_objets"]

        if dry_run:
            self.stdout.write(self.style.WARNING("Dry run mode enabled"))

        objets = Objet.objects.prefetch_related("sous_categorie").all()

        synonyme_found = 0
        synonyme_not_found = 0
        synonymes_to_create = []
        sous_categories_unsync = []
        for objet in objets:
            synonymes = Synonyme.objects.filter(slug=objet.slug)
            if synonymes.count() > 1:
                raise Exception(
                    "Impossible ! Plusieurs synonymes trouvés pour le même slug "
                    f"{objet.slug}"
                )
            elif synonymes.count() == 1:
                synonyme_found += 1
                objet_sous_categorie_code = objet.sous_categorie.code
                synonyme_sous_categorie_codes = [
                    sc.code for sc in synonymes.first().produit.sous_categories.all()
                ]
                if set([objet_sous_categorie_code]) != set(
                    synonyme_sous_categorie_codes
                ):

                    sous_categories_unsync.append(
                        {
                            "slug": objet.slug,
                            "objet_sous_categorie_code": objet_sous_categorie_code,
                            "synonyme_sous_categorie_codes": (
                                synonyme_sous_categorie_codes
                            ),
                        }
                    )

            else:
                synonyme_not_found += 1
                self.stdout.write(
                    self.style.WARNING(
                        f"Synonyme non trouvé pour l'objet {objet.libelle} "
                        f"({objet.slug})"
                    )
                )
                synonymes_to_create.append(
                    {
                        "libelle": objet.libelle,
                        "sous_categorie": objet.sous_categorie.code,
                    }
                )
        sous_categories = list(set(s["sous_categorie"] for s in synonymes_to_create))

        self.stdout.write(self.style.SUCCESS(f"Synonymes trouvés: {synonyme_found}"))
        self.stdout.write(
            self.style.WARNING(f"Synonymes non trouvés: {synonyme_not_found}")
        )

        synonymes_by_sous_categorie = {}
        produits_by_sous_categorie = {}
        for sous_categorie in sous_categories:
            synonymes_by_sous_categorie[sous_categorie] = list(
                Synonyme.objects.filter(produit__sous_categories__code=sous_categorie)
                .values_list("nom", flat=True)
                .distinct()
            )
            produits_by_sous_categorie[sous_categorie] = list(
                Produit.objects.filter(sous_categories__code=sous_categorie)
                .values_list("nom", flat=True)
                .distinct()
            )

        objet_slugs = list(objets.values_list("slug", flat=True))
        synonymes_sans_objets = (
            Synonyme.objects.prefetch_related("produit")
            .exclude(slug__in=objet_slugs)
            .order_by("produit__nom")
        )
        synonymes_sans_objets_prepare = []
        for synonyme in synonymes_sans_objets:
            synonymes_sans_objets_prepare.append(
                {
                    "produit": synonyme.produit.nom,
                    "slug": synonyme.slug,
                    "nom": synonyme.nom,
                    "synonyme_sous_categorie_codes": " | ".join(
                        [sc.code for sc in synonyme.produit.sous_categories.all()]
                    ),
                }
            )

        for synonyme in synonymes_to_create:
            synonyme["produits de la même sous-catégorie"] = " | ".join(
                produits_by_sous_categorie[synonyme["sous_categorie"]]
            )
            synonyme["synonymes de la même sous-catégorie"] = " | ".join(
                synonymes_by_sous_categorie[synonyme["sous_categorie"]]
            )

        if len(sous_categories_unsync) > 0:
            self.stdout.write(
                self.style.WARNING(
                    f"{len(sous_categories_unsync)} Objets et Synonymes de même slug"
                    " mais n'appartenant pas aux mêmes sous-categories"
                )
            )
            synonymes_plusieurs_sous_categories = {
                s["slug"]: s["synonyme_sous_categorie_codes"]
                for s in sous_categories_unsync
                if len(s["synonyme_sous_categorie_codes"]) > 1
            }

            if len(synonymes_plusieurs_sous_categories) > 0:
                self.stdout.write(
                    self.style.WARNING(
                        (
                            f"{len(synonymes_plusieurs_sous_categories)} synonymes avec"
                            " plusieurs sous-catégories : "
                        )
                        + ", ".join(synonymes_plusieurs_sous_categories.keys())
                    )
                )
                # self.stdout.write(
                #     self.style.WARNING(str(synonymes_plusieurs_sous_categories))
                # )

            # print(sous_categories_unsync)

        # Écriture dans le fichier CSV
        output_path = Path(output_objets_file)
        with open(output_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(
                f,
                fieldnames=[
                    "libelle",
                    "sous_categorie",
                    "produits de la même sous-catégorie",
                    "synonymes de la même sous-catégorie",
                ],
            )
            writer.writeheader()
            writer.writerows(synonymes_to_create)

        self.stdout.write(
            self.style.SUCCESS(f"CSV créé avec succès : {output_path.absolute()}")
        )

        for s in sous_categories_unsync:
            s["synonyme_sous_categorie_codes"] = " | ".join(
                s["synonyme_sous_categorie_codes"]
            )

        # Écriture dans le fichier CSV
        output_path = Path(output_conflict_file)
        with open(output_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(
                f,
                fieldnames=[
                    "slug",
                    "objet_sous_categorie_code",
                    "synonyme_sous_categorie_codes",
                ],
            )
            writer.writeheader()
            writer.writerows(sous_categories_unsync)

        self.stdout.write(
            self.style.SUCCESS(f"CSV créé avec succès : {output_path.absolute()}")
        )

        output_path = Path(output_synonymes_sans_objets_file)
        with open(output_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(
                f,
                fieldnames=["produit", "slug", "nom", "synonyme_sous_categorie_codes"],
            )
            writer.writeheader()
            writer.writerows(synonymes_sans_objets_prepare)

        self.stdout.write(
            self.style.SUCCESS(f"CSV créé avec succès : {output_path.absolute()}")
        )
