"""Deterministic, self-contained review cohorte for the Playwright e2e suite
and for manual testing on the sample database.

Unlike `seed_review_demo` (which builds on existing acteurs), this command
creates its own acteurs so it works against an empty sample database, and
uses stable identifiers so tests can target known rows and assert exact
counts. Idempotent: the previous e2e cohorte and its acteurs are removed
and rebuilt.

Data scheme (NB_GROUPES = 24, indices 0..23):
- nom suggestion on every groupe.
- telephone suggestion on every groupe; value starts with "07" when
  index % 3 == 0 (→ 8 of 24), else "02" — drives the query builder test.
- url suggestion only when index is even (→ 12 of 24) — drives the column
  filter / champ tests.
- identifiant_unique contains "morbihan" for indices 0..3 (which stay
  À valider) — drives the search (q) test (4 matches).
- the last 4 indices start decided (2 ACCEPTED, 2 REJECTED); the rest stay
  À valider; drives the statut-filter test (20 à valider, 2+2 decided).
  Pre-decided rows are placed at the END so the searchable « morbihan »
  rows remain À valider and visible under the default filter.
"""

from data.models.suggestion import (
    SuggestionAction,
    SuggestionGroupe,
    SuggestionStatut,
    SuggestionUnitaire,
)
from data.models.suggestion import (
    SuggestionCohorte as Cohorte,
)
from django.contrib.gis.geos import Point
from django.core.management.base import BaseCommand
from django.db import transaction
from qfdmo.models.acteur import Acteur, ActeurType

E2E_IDENTIFIANT_ACTION = "e2e_revue_cohorte"
E2E_ACTEUR_TYPE_CODE = "e2e_review_type"
E2E_ACTEUR_PREFIX = "e2e_review_acteur_"
NB_GROUPES = 24
NB_SEARCHABLE = 4  # indices 0..3 carry « morbihan » in their id
NB_ACCEPTED = 2  # indices 0..1 pre-accepted
NB_REJECTED = 2  # indices 2..3 pre-rejected
TELEPHONE_07_COUNT = len([i for i in range(NB_GROUPES) if i % 3 == 0])
URL_COUNT = len([i for i in range(NB_GROUPES) if i % 2 == 0])


def _identifiant(index: int) -> str:
    region = "morbihan" if index < NB_SEARCHABLE else "ailleurs"
    return f"{E2E_ACTEUR_PREFIX}{region}_{index:02d}"


def _telephone(index: int) -> str:
    prefix = "07" if index % 3 == 0 else "02"
    return f"{prefix} 99 {index:02d} {index:02d} {index:02d}"


def _statut(index: int) -> str:
    # pre-decided rows live at the end so the low « morbihan » indices stay
    # À valider (visible under the default filter for the search test)
    if index >= NB_GROUPES - NB_ACCEPTED:
        return SuggestionStatut.ATRAITER
    if index >= NB_GROUPES - NB_ACCEPTED - NB_REJECTED:
        return SuggestionStatut.REJETEE
    return SuggestionStatut.AVALIDER


class Command(BaseCommand):
    help = (
        "Seed a deterministic, self-contained review cohorte for e2e tests "
        "and manual review-screen testing on the sample DB (idempotent)."
    )

    @transaction.atomic
    def handle(self, *args, **options):
        # tear down the previous run (cascades to groupes + unitaires)
        Cohorte.objects.filter(identifiant_action=E2E_IDENTIFIANT_ACTION).delete()
        Acteur.objects.filter(identifiant_unique__startswith=E2E_ACTEUR_PREFIX).delete()

        acteur_type, _ = ActeurType.objects.get_or_create(code=E2E_ACTEUR_TYPE_CODE)
        cohorte = Cohorte.objects.create(
            identifiant_action=E2E_IDENTIFIANT_ACTION,
            identifiant_execution="2026-01-01T00:00:00",
            type_action=SuggestionAction.SOURCE_MODIFICATION,
        )

        for index in range(NB_GROUPES):
            identifiant = _identifiant(index)
            statut = _statut(index)
            acteur = Acteur.objects.create(
                identifiant_unique=identifiant,
                nom=f"Acteur e2e {index:02d}",
                location=Point(2.35, 48.85),
                acteur_type=acteur_type,
            )
            groupe = SuggestionGroupe.objects.create(
                suggestion_cohorte=cohorte, acteur=acteur, statut=statut
            )
            fields = {
                "nom": f"Acteur e2e {index:02d} (corrigé)",
                "telephone": _telephone(index),
            }
            if index % 2 == 0:
                fields["url"] = f"https://exemple-{index:02d}.example.fr"
            for champ, valeur in fields.items():
                SuggestionUnitaire.objects.create(
                    suggestion_groupe=groupe,
                    suggestion_modele="Acteur",
                    acteur=acteur,
                    champs=[champ],
                    valeurs=[valeur],
                    statut=statut,
                )

        self.stdout.write(
            self.style.SUCCESS(
                f"E2E cohorte #{cohorte.id} créée ({NB_GROUPES} groupes, "
                f"{TELEPHONE_07_COUNT} tel 07, {URL_COUNT} url, "
                f"{NB_SEARCHABLE} « morbihan ») : "
                f"/data/cohorte/{cohorte.id}/review/"
            )
        )
        # machine-readable last line so the e2e harness can capture the id
        self.stdout.write(f"COHORTE_ID={cohorte.id}")
