from django.core.management.base import BaseCommand

from qfdmo.models.action import GroupeAction

# Figma « DSM Assistant V2 » (24382:53).
LIBELLES_COURTS = {
    "reparer": "Réparer",
    "donner_echanger_rapporter": "Donner",
    "emprunter_preter_louer": "Prêter",
    "vendre_acheter": "Vendre",
    "trier": "Déposer",
}


class Command(BaseCommand):
    help = "Set the short label of each geste (GroupeAction.libelle_court)."

    def handle(self, *args, **options):
        updated = sum(
            GroupeAction.objects.filter(code=code).update(libelle_court=libelle)
            for code, libelle in LIBELLES_COURTS.items()
        )
        self.stdout.write(f"{updated} groupe(s) d'action mis à jour")
