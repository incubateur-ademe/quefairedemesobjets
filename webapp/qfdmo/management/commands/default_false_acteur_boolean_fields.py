import argparse
import logging
from collections.abc import Callable

from django.core.management.base import BaseCommand
from qfdmo.models.acteur import Acteur, DisplayedActeur, VueActeur

logger = logging.getLogger(__name__)

BOOLEAN_FIELDS = ("exclusivite_de_reprisereparation", "uniquement_sur_rdv")
MODELS = (Acteur, DisplayedActeur, VueActeur)
BATCH_SIZE = 10_000


def default_false_acteur_boolean_fields(
    *,
    dry_run: bool = False,
    batch_size: int = BATCH_SIZE,
    log_progress: Callable[[str], None] | None = None,
) -> dict[str, dict[str, int]]:
    """Replace NULL values with False on acteur boolean fields."""

    def _log(message: str) -> None:
        logger.info(message)
        if log_progress is not None:
            log_progress(message)

    stats: dict[str, dict[str, int]] = {}

    for model in MODELS:
        model_name = model.__name__
        stats[model_name] = {}

        for field in BOOLEAN_FIELDS:
            null_queryset = model.objects.filter(**{field: None})
            total = null_queryset.count()
            stats[model_name][field] = total

            prefix = "DRY RUN " if dry_run else ""
            _log(f"{prefix}{model_name}.{field}: {total} valeurs NULL détectées")

            if dry_run or total == 0:
                continue

            null_queryset.update(**{field: False})
            _log(f"{model_name}.{field}: {total} mis à jour")

    return stats


class Command(BaseCommand):
    help = (
        "Remplace les valeurs NULL par False sur exclusivite_de_reprisereparation "
        "et uniquement_sur_rdv pour Acteur, DisplayedActeur et VueActeur"
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            help="Affiche les compteurs sans modifier la base",
            action=argparse.BooleanOptionalAction,
            default=False,
        )
        parser.add_argument(
            "--batch-size",
            help="Nombre d'enregistrements mis à jour par lot",
            type=int,
            default=BATCH_SIZE,
        )

    def handle(self, *args, **options):
        dry_run = options["dry_run"]
        batch_size = options["batch_size"]

        self.stdout.write(
            self.style.WARNING("Démarrage de la mise à jour des champs booléens")
        )
        if dry_run:
            self.stdout.write(self.style.WARNING("Mode dry-run activé"))

        stats = default_false_acteur_boolean_fields(
            dry_run=dry_run,
            batch_size=batch_size,
            log_progress=self.stdout.write,
        )

        total_updated = sum(sum(fields.values()) for fields in stats.values())
        suffix = "à mettre à jour" if dry_run else "mis à jour"
        self.stdout.write(
            self.style.SUCCESS(
                f"Terminé : {total_updated} enregistrements {suffix} au total"
            )
        )
