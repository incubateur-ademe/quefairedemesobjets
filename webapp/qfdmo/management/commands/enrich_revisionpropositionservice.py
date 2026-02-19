import argparse

from django.core.management.base import BaseCommand
from django.db.models import QuerySet

from qfdmo.models.acteur import (
    Acteur,
    RevisionActeur,
    RevisionPropositionService,
    Source,
)
from qfdmo.models.action import Action


def ps_by_action(propositionservices: QuerySet):
    return {
        p.action.code: [sscat for sscat in p.sous_categories.all()]
        for p in propositionservices
    }


class Command(BaseCommand):
    help = """
    Correction des propositions de service révisiées d'une source
    Pour l'ensemble des révision de proposition de service,
    ajouter les propositions de service présenste dans l'acteur source si celle-ci
    n'existe pas dans la révision de proposition de service.
    Cette commande est utile quand une source à ajouté des propositions de service
    dans l'acteur source et que ces proposition n'ont pas été ajoutées dans
    la révision de proposition de service.
    """

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            help="Run command without writing changes to the database",
            action=argparse.BooleanOptionalAction,
            default=False,
        )
        parser.add_argument(
            "--source_code",
            help="code de la source concernée",
            type=str,
            required=True,
        )

    def handle(self, *args, **options):
        dry_run = options["dry_run"]
        source_code = options["source_code"]

        try:
            source = Source.objects.get(code=source_code)
        except Source.DoesNotExist:
            self.stdout.write(self.style.ERROR(f"Source {source_code} non trouvée"))

        for acteur in Acteur.objects.filter(source=source):
            try:
                revision_acteur = RevisionActeur.objects.get(
                    identifiant_unique=acteur.identifiant_unique
                )
            except RevisionActeur.DoesNotExist:
                continue

            ps_acteur_by_action = ps_by_action(acteur.proposition_services.all())
            rps_acteur_by_action = ps_by_action(
                revision_acteur.proposition_services.all()
            )

            pss_to_add = []
            pss_to_update = []
            for action_code, ps_acteur_sscats in ps_acteur_by_action.items():
                if action_code not in rps_acteur_by_action:
                    pss_to_add.append(
                        {
                            action_code: ps_acteur_sscats,
                        }
                    )
                    continue

                if sscat := set(ps_acteur_sscats) - set(
                    rps_acteur_by_action[action_code]
                ):
                    pss_to_update.append(
                        {
                            action_code: sscat,
                        }
                    )

            action_by_code = {a.code: a for a in Action.objects.all()}
            if pss_to_add or pss_to_update:
                message = f"Acteur {acteur.identifiant_unique}:\n"
                if pss_to_add:
                    displayed_ps = [
                        {k: [s.code for s in v] for k, v in ps.items()}
                        for ps in pss_to_add
                    ]
                    message += "Ajout des proposition de services\n"
                    message += f"{displayed_ps}"
                if pss_to_update:
                    displayed_ps = [
                        {k: [s.code for s in v] for k, v in ps.items()}
                        for ps in pss_to_update
                    ]
                    message += "Mise à jour des proposition de services\n"
                    message += f"{displayed_ps}"
                self.stdout.write(self.style.WARNING(message))
                if not dry_run:
                    if pss_to_add:
                        for ps_to_add in pss_to_add:
                            for action_code, ps_acteur_sscats in ps_to_add.items():
                                ps = RevisionPropositionService.objects.create(
                                    action=action_by_code[action_code],
                                    acteur=revision_acteur,
                                )
                                ps.sous_categories.add(*ps_acteur_sscats)
                    if pss_to_update:
                        for ps_to_update in pss_to_update:
                            for action_code, ps_acteur_sscats in ps_to_update.items():
                                ps = RevisionPropositionService.objects.get(
                                    action=action_by_code[action_code],
                                    acteur=revision_acteur,
                                )
                                ps.sous_categories.add(*ps_acteur_sscats)
