from django.core.management.base import BaseCommand
from django.db.models import Count

from qfdmo.models.acteur import Acteur, RevisionActeur, RevisionPropositionService


class Command(BaseCommand):
    help = "Export Ressources using CSV format"

    def handle(self, *args, **options):
        parent_ids = RevisionActeur.objects.values_list("parent_id", flat=True).exclude(
            parent_id__isnull=True
        )
        parent_ids = list(set(list(parent_ids)))
        revision_acteurs = (
            RevisionActeur.objects.annotate(num=Count("proposition_services"))
            .filter(num=0)
            .exclude(identifiant_unique__in=parent_ids)
            .exclude(statut="SUPPRIME")
        )
        for revision_acteur in revision_acteurs:
            acteur = Acteur.objects.get(
                identifiant_unique=revision_acteur.identifiant_unique
            )

            print(f"Creating revision object for {acteur.identifiant_unique}")

            for proposition_service in acteur.proposition_services.all():  # type: ignore
                revision_proposition_service = (
                    RevisionPropositionService.objects.create(
                        acteur=revision_acteur,
                        action_id=proposition_service.action_id,
                    )
                )
                revision_proposition_service.sous_categories.add(
                    *proposition_service.sous_categories.all()
                )
            for label in acteur.labels.all():
                revision_acteur.labels.add(label)
            for acteur_service in acteur.acteur_services.all():
                revision_acteur.acteur_services.add(acteur_service)
