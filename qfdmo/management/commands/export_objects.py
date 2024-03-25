## DEPRECATED
## Won't be used anymore

from django.core.management.base import BaseCommand

from qfdmo.admin import (
    ActeurResource,
    DisplayedActeurResource,
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
                "displayed_acteur",
                "objet",
                "proposition_service",
                "revision_acteur",
                "revision_proposition_service",
            ],
        )

    def handle(self, *args, **options):
        object = options.get("object")
        ressource_by_object: dict = {
            "acteur": ActeurResource,
            "displayed_acteur": DisplayedActeurResource,
            "objet": ObjetResource,
            "proposition_service": PropositionServiceResource,
            "revision_acteur": RevisionActeurResource,
            "revision_proposition_service": RevisionPropositionServiceResource,
        }
        ressource_class = ressource_by_object[object]
        dataset = ressource_class(nb_object_max=0).export()

        print(dataset.csv)
