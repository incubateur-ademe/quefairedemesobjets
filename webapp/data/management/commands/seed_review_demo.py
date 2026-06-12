import random

from data.models.suggestion import (
    SuggestionAction,
    SuggestionCohorte,
    SuggestionGroupe,
    SuggestionUnitaire,
)
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from qfdmo.models.acteur import Acteur

DEMO_IDENTIFIANT_ACTION = "demo_revue_cohorte"

FIELD_SUGGESTIONS = {
    "nom": lambda acteur, i: f"{acteur.nom} (mis à jour)",
    "telephone": lambda acteur, i: (
        f"02 99 {i % 90 + 10:02d} {i % 80 + 10:02d} {i % 70 + 10:02d}"
    ),
    "url": lambda acteur, i: f"https://exemple-{i}.example.fr",
    "adresse": lambda acteur, i: f"{i % 120 + 1} rue de la Démonstration",
}


class Command(BaseCommand):
    help = (
        "Crée une cohorte de démonstration pour l'écran de revue "
        "(/data/cohorte/<id>/review/) à partir des acteurs en base. "
        "Idempotent : la cohorte de démo précédente est remplacée."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--groupes",
            type=int,
            default=50,
            help="Nombre de groupes de suggestions à créer (défaut : 50)",
        )

    def handle(self, *args, **options):
        nb_groupes = options["groupes"]
        acteurs = list(Acteur.objects.order_by("identifiant_unique")[:nb_groupes])
        if not acteurs:
            raise CommandError(
                "Aucun acteur en base : lancez d'abord `make seed-database`."
            )

        SuggestionCohorte.objects.filter(
            identifiant_action=DEMO_IDENTIFIANT_ACTION
        ).delete()
        cohorte = SuggestionCohorte.objects.create(
            identifiant_action=DEMO_IDENTIFIANT_ACTION,
            identifiant_execution=timezone.now().isoformat(),
            type_action=SuggestionAction.SOURCE_MODIFICATION,
        )

        # Seeded random: same acteurs always get the same suggested fields,
        # so reruns are comparable
        rng = random.Random(42)
        for index, acteur in enumerate(acteurs):
            groupe = SuggestionGroupe.objects.create(
                suggestion_cohorte=cohorte, acteur=acteur
            )
            fields = rng.sample(
                sorted(FIELD_SUGGESTIONS), k=rng.randint(1, len(FIELD_SUGGESTIONS) - 1)
            )
            for field in fields:
                SuggestionUnitaire.objects.create(
                    suggestion_groupe=groupe,
                    suggestion_modele="Acteur",
                    acteur=acteur,
                    champs=[field],
                    valeurs=[FIELD_SUGGESTIONS[field](acteur, index)],
                )

        self.stdout.write(
            self.style.SUCCESS(
                f"Cohorte #{cohorte.id} créée avec {len(acteurs)} groupes : "
                f"/data/cohorte/{cohorte.id}/review/"
            )
        )
