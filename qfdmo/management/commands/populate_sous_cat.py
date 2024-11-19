from django.core.management.base import BaseCommand

from qfdmo.models.acteur import Acteur, PropositionService, RevisionPropositionService
from qfdmo.models.categorie_objet import SousCategorieObjet

MAPPINGS = [
    {
        "existing_sous_categorie": "outil de bricolage et jardinage",
        "new_sous_categories": [
            "Machines et appareils motorises thermiques",
            "Outil de bricolage et jardinage electrique",
        ],
        "actions": ["reparer", "donner", "vendre", "louer"],
    }
]


def assign_new_sous_cat(dry_run: bool = False) -> None:
    # Révision de proposition de service
    # sur proposition de service, si pas revision de proposition de service alors on
    #  crée une révision et on corrige les revision de proposition de service
    for mapping in MAPPINGS:
        existing_sous_categorie = mapping["existing_sous_categorie"]

        # créer les RévisionActeur pour les acteurs qui n'en ont pas et qui sont
        # concernés par l'ajoutde sous catégories
        acteur_ids = (
            PropositionService.objects.filter(
                sous_categories__code=existing_sous_categorie,
                action__code__in=mapping["actions"],
            )
            .exclude(
                acteur_id__in=RevisionPropositionService.objects.values_list(
                    "acteur_id", flat=True
                )
            )
            .values_list("acteur_id", flat=True)
        )
        acteurs = Acteur.objects.filter(id__in=acteur_ids)
        for acteur in acteurs:
            acteur.get_or_create_revision()

        # Collecter les nouvelles sous catégories
        new_sous_categorie_objets = [
            SousCategorieObjet.objects.get(code=code)
            for code in mapping["new_sous_categories"]
        ]

        # Ajouter les nouvelles sous catégories aux RevisionPropositionService
        prop_services = RevisionPropositionService.objects.filter(
            sous_categories__code=existing_sous_categorie,
            action__code__in=mapping["actions"],
        )
        for prop_service in prop_services:
            prop_service.sous_categories.add(new_sous_categorie_objets)


class Command(BaseCommand):
    help = "Get info from INSEE and save proposition of correction"

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            help="Dry run",
            action="store_true",
        )

    def handle(self, *args, **options):
        dry_run = options.get("dry_run")
        assign_new_sous_cat(dry_run=dry_run)
