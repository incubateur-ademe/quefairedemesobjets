"""Deterministic, self-contained review cohorte for the Playwright e2e suite.

Unlike `seed_review_demo` (which builds on existing acteurs), this command
creates its own acteurs so it works against an empty sample database, and
uses stable identifiers so the test can target known rows. Idempotent: the
previous e2e cohorte and its acteurs are removed and rebuilt.
"""

from data.models.suggestion import (
    SuggestionAction,
    SuggestionCohorte,
    SuggestionGroupe,
    SuggestionUnitaire,
)
from django.contrib.gis.geos import Point
from django.core.management.base import BaseCommand
from django.db import transaction
from qfdmo.models.acteur import Acteur, ActeurType

E2E_IDENTIFIANT_ACTION = "e2e_revue_cohorte"
E2E_ACTEUR_TYPE_CODE = "e2e_review_type"
E2E_ACTEUR_PREFIX = "e2e_review_acteur_"
NB_GROUPES = 12


# Stable per-acteur suggested values, indexed by position. The telephone
# values are crafted so the focus-mode query builder « commence par 07 »
# matches a known subset (positions 0, 3, 6, 9).
def _telephone(index: int) -> str:
    prefix = "07" if index % 3 == 0 else "02"
    return f"{prefix} 99 {index:02d} {index:02d} {index:02d}"


class Command(BaseCommand):
    help = "Seed a deterministic review cohorte for e2e tests (idempotent)."

    @transaction.atomic
    def handle(self, *args, **options):
        # tear down the previous run (cascades to groupes + unitaires)
        SuggestionCohorte.objects.filter(
            identifiant_action=E2E_IDENTIFIANT_ACTION
        ).delete()
        Acteur.objects.filter(identifiant_unique__startswith=E2E_ACTEUR_PREFIX).delete()

        acteur_type, _ = ActeurType.objects.get_or_create(code=E2E_ACTEUR_TYPE_CODE)
        cohorte = SuggestionCohorte.objects.create(
            identifiant_action=E2E_IDENTIFIANT_ACTION,
            identifiant_execution="2026-01-01T00:00:00",
            type_action=SuggestionAction.SOURCE_MODIFICATION,
        )

        for index in range(NB_GROUPES):
            identifiant = f"{E2E_ACTEUR_PREFIX}{index:02d}"
            acteur = Acteur.objects.create(
                identifiant_unique=identifiant,
                nom=f"Acteur e2e {index:02d}",
                location=Point(2.35, 48.85),
                acteur_type=acteur_type,
            )
            groupe = SuggestionGroupe.objects.create(
                suggestion_cohorte=cohorte, acteur=acteur
            )
            SuggestionUnitaire.objects.create(
                suggestion_groupe=groupe,
                suggestion_modele="Acteur",
                acteur=acteur,
                champs=["nom"],
                valeurs=[f"Acteur e2e {index:02d} (corrigé)"],
            )
            SuggestionUnitaire.objects.create(
                suggestion_groupe=groupe,
                suggestion_modele="Acteur",
                acteur=acteur,
                champs=["telephone"],
                valeurs=[_telephone(index)],
            )

        self.stdout.write(
            self.style.SUCCESS(
                f"E2E cohorte #{cohorte.id} créée ({NB_GROUPES} groupes) : "
                f"/data/cohorte/{cohorte.id}/review/"
            )
        )
        # machine-readable last line so the e2e harness can capture the id
        self.stdout.write(f"COHORTE_ID={cohorte.id}")
