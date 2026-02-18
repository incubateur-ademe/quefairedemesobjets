import argparse

from django.core.management.base import BaseCommand

from qfdmo.models.acteur import PropositionService, RevisionPropositionService
from qfdmo.models.categorie_objet import SousCategorieObjet


class Command(BaseCommand):
    help = """
    Ajout d'une sous-catégorie aux propositions de service qui en contient une autre
    Cette commande est utile quand on ajoute une nouvelle sous-catégorie car on a besoin
    de plus de détails, on veut alors pouvoir ajouter cette nouvelle sous-catégorie
    en masse aux propositions de service qui en contient une sous-catégorie spécifique.

    ex : on ajoute la sous-catégorie "Poêle et Casserole" aux propositions de service
    qui en contiennent la sous-catégorie "Vaisselle"
    """

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            help="Run command without writing changes to the database",
            action=argparse.BooleanOptionalAction,
            default=False,
        )
        parser.add_argument(
            "--new_sous_categorie_code",
            help="code de la nouvelle sous-catégorie à ajouter",
            type=str,
            required=True,
        )
        parser.add_argument(
            "--origin_sous_categorie_code",
            help="""
            code de la sous-catégorie d'origine, on ajoutera la nouvelle sous-catégorie
            à toutes les propositions de service qui en contiennent cette sous-catégorie
            """,
            type=str,
            required=True,
        )

    def handle(self, *args, **options):
        dry_run = options["dry_run"]
        new_sous_categorie_code = options["new_sous_categorie_code"]
        origin_sous_categorie_code = options["origin_sous_categorie_code"]

        ps_classes = [PropositionService, RevisionPropositionService]
        nb_updated = {cls.__name__: 0 for cls in ps_classes}

        new_sous_categorie = SousCategorieObjet.objects.get(
            code=new_sous_categorie_code
        )
        for cls in ps_classes:
            for ps in (
                cls.objects.prefetch_related("action")
                .filter(sous_categories__code=origin_sous_categorie_code)
                .exclude(sous_categories__code=new_sous_categorie_code)
            ):
                self.stdout.write(
                    self.style.SUCCESS(
                        f"{cls.__name__} {dry_run and 'DRY RUN ' or ''}: "
                        f"Updating {ps.acteur_id} - {ps.action.code}"
                    )
                )
                nb_updated[cls.__name__] += 1
                if not dry_run:
                    ps.sous_categories.add(new_sous_categorie)

        for cls in ps_classes:
            self.stdout.write(
                self.style.SUCCESS(
                    f"{cls.__name__}: Updated {nb_updated[cls.__name__]}"
                    " propositions de service"
                )
            )
