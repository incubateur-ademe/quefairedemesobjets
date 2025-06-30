from django.core.management import call_command
from django.core.management.base import BaseCommand

from qfdmo.models.acteur import DisplayedPropositionService


class Command(BaseCommand):
    def handle(self, *args, **options):
        pks = ",".join(
            [
                "alrebobinage__altech_distribution_sce_154142_reparation_0626645539",
                "locarmor_658_locations",
                "communautelvao_LWTYYUPBDMWM",
                "6554f1bb-82d2-567f-8453-eec5405e5b5d",  # pragma: allowlist secret
                "65791ef2-bb37-4569-b011-8cece03dcdcf",  # pragma: allowlist secret
                "antiquites_du_poulbenn_152575_reparation",
                "refashion_TLC-REFASHION-PAV-3445001",  # pragma: allowlist secret
                "communautelvao_VBOFDJDBOCTW",
                # pragma: allowlist nextline secret
                "refashion_TLC-REFASHION-REP-603665791852778329",
                "ocad3e_SGS-02069",
            ]
        )
        call_command(
            "dumpdata",
            "qfdmo.displayedacteur",
            pks=pks,
            output="qfdmo/fixtures/acteurs.json",
        )
        ps_pks = DisplayedPropositionService.objects.filter(
            acteur__pk__in=pks
        ).values_list("pk", flat=True)
        call_command(
            "dumpdata",
            "qfdmo.displayedpropositionservice",
            pks=ps_pks,
            output="qfdmo/fixtures/propositions_services.json",
        )
