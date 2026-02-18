from django.core.management.base import BaseCommand

from qfdmo.models.acteur import Acteur, RevisionActeur, RevisionPropositionService


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
        nb_acteur_limit = options.get("limit")
        nb_processed = 0
        total_revisionacteur = RevisionActeur.objects.count()
        for revisionacteur in RevisionActeur.objects.all():
            acteur = Acteur.objects.filter(
                identifiant_unique=revisionacteur.identifiant_unique
            ).first()
            if not acteur:
                print(f"Acteur {revisionacteur.identifiant_unique} not found")
                continue
            if nb_processed % 100 == 0:
                print(f"Processed {nb_processed}/{total_revisionacteur}")
            if revisionacteur.labels.count() == 0:
                for label in acteur.labels.all():
                    revisionacteur.labels.add(label)

            if revisionacteur.acteur_services.count() == 0:
                for acteur_service in acteur.acteur_services.all():
                    revisionacteur.acteur_services.add(acteur_service)

            if revisionacteur.proposition_services.count() == 0:

                for proposition_service in acteur.proposition_services.all():
                    revision_proposition_service = (
                        RevisionPropositionService.objects.create(
                            acteur=revisionacteur,
                            action_id=proposition_service.action_id,
                        )
                    )
                    revision_proposition_service.sous_categories.add(
                        *proposition_service.sous_categories.all()
                    )

            nb_processed += 1
            if nb_acteur_limit and nb_processed > nb_acteur_limit:
                break
