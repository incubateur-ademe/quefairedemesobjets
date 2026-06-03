import argparse

from django.core.management.base import BaseCommand
from django.db import transaction
from qfdmo.models.acteur import Acteur, PropositionService, RevisionActeur

#'+ report de revision sur source si pas de proposition de service sur l'acteur importé


# `+ filtre sur statut
SOURCE_CODES = [
    "ademedigitaux",
    "ademelocales",
    "ademelocation",
    "ademenationales",
    "bibliotheques",
    "communautelvao",
    "lvao",
    "recyclivrebal",
    "sinoe",
]


class Command(BaseCommand):
    help = "Realign acteur and revision proposition service"

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            help="Run command without writing changes to the database",
            action=argparse.BooleanOptionalAction,
            default=False,
        )
        parser.add_argument(
            "--for-selected-sources",
            help="Copy proposition service from revision for selected sources",
            action=argparse.BooleanOptionalAction,
            default=False,
        )
        parser.add_argument(
            "--if-empty",
            help=(
                "Copy proposition service from revision if acteur has no proposition"
                " service"
            ),
            action=argparse.BooleanOptionalAction,
            default=False,
        )

    def handle(self, *args, **options):
        dry_run = options["dry_run"]
        for_selected_sources = options["for_selected_sources"]
        if_empty = options["if_empty"]
        if for_selected_sources:
            self.copy_proposition_service_from_revision_for_selected_sources(
                dry_run=dry_run
            )
        if if_empty:
            self.copy_proposition_service_from_revision_if_empty(dry_run=dry_run)

    def _copy_ps_from_revision_to_acteur(
        self, acteur: Acteur, revision_acteur: RevisionActeur, dry_run: bool
    ):
        with transaction.atomic():
            if not dry_run:
                PropositionService.objects.filter(acteur=acteur).delete()
            for (
                revision_proposition_service
            ) in revision_acteur.proposition_services.all():
                if not dry_run:
                    proposition_service = PropositionService.objects.create(
                        acteur=acteur,
                        action=revision_proposition_service.action,
                    )
                    proposition_service.sous_categories.set(
                        revision_proposition_service.sous_categories.all()
                    )
                else:
                    self.stdout.write(
                        self.style.SUCCESS(
                            "DRY RUN: Would have copied proposition service"
                            " from revision for acteur "
                            f"{acteur.identifiant_unique}"
                        )
                    )

    def copy_proposition_service_from_revision_for_selected_sources(
        self,
        source_codes: list[str] = SOURCE_CODES,
        dry_run: bool = False,
    ):
        self.stdout.write(
            self.style.SUCCESS(
                "Copying proposition service from revision for selected sources"
                f"{' [DRY RUN]' if dry_run else ''}"
            )
        )
        count = 0
        total = Acteur.objects.filter(source__code__in=source_codes).count()
        for acteur in Acteur.objects.filter(source__code__in=source_codes):
            try:
                revision_acteur = RevisionActeur.objects.get(
                    identifiant_unique=acteur.identifiant_unique
                )
            except RevisionActeur.DoesNotExist:
                continue
            self._copy_ps_from_revision_to_acteur(acteur, revision_acteur, dry_run)
            count += 1
            if count % 100 == 0:
                self.stdout.write(
                    self.style.SUCCESS(f"Processed {count} / {total} acteurs")
                )

    def copy_proposition_service_from_revision_if_empty(
        self,
        dry_run: bool = False,
    ):
        self.stdout.write(
            self.style.SUCCESS(
                "Copying proposition service from revision if acteur has no proposition"
                " service"
                f"{' [DRY RUN]' if dry_run else ''}"
            )
        )
        count = 0
        total = Acteur.objects.filter(proposition_services__isnull=True).count()
        acteurs = Acteur.objects.filter(proposition_services__isnull=True)
        for acteur in acteurs:
            try:
                revision_acteur = RevisionActeur.objects.get(
                    identifiant_unique=acteur.identifiant_unique
                )
            except RevisionActeur.DoesNotExist:
                continue
            self._copy_ps_from_revision_to_acteur(acteur, revision_acteur, dry_run)
            count += 1
            if count % 100 == 0:
                self.stdout.write(
                    self.style.SUCCESS(f"Processed {count} / {total} acteurs")
                )
