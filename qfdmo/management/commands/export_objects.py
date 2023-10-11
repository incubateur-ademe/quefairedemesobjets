from django.core.management.base import BaseCommand

from qfdmo.admin import ActeurResource
from qfdmo.admin.acteur import (
    PropositionServiceResource,
    RevisionActeurResource,
    RevisionPropositionServiceResource,
)
from qfdmo.admin.categorie_objet import ObjetResource


class Command(BaseCommand):
    help = "Export Ressources using CSV format"

    def add_arguments(self, parser):
        parser.add_argument(
            "--object",
            help="object to export",
            choices=[
                "acteur",
                "revision_acteur",
                "objet",
                "proposition_service",
                "revision_proposition_service",
            ],
        )

    def handle(self, *args, **options):
        object = options.get("object")
        ressource_by_object: dict = {
            "acteur": ActeurResource,
            "revision_acteur": RevisionActeurResource,
            "objet": ObjetResource,
            "proposition_service": PropositionServiceResource,
            "revision_proposition_service": RevisionPropositionServiceResource,
        }
        ressource_class = ressource_by_object[object]
        dataset = ressource_class().export()

        print(dataset.csv)
