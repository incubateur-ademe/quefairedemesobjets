from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from qfdmd.legacy_migration import (
    MigrationError,
    get_or_create_legacy_index_page,
    migrate_produit,
)
from qfdmd.models import LEGACY_PRODUIT_INDEX_SLUG, Produit


class _Rollback(Exception):
    """Raised to roll back the surrounding transaction on --dry-run."""


class Command(BaseCommand):
    help = (
        "Migre les Produit legacy vers des ProduitPage : copie les champs "
        "(préfixés legacy_), crée les pages sous l'index /dechet, importe "
        "les synonymes restants comme SearchTags "
        "(legacy_imported_as_search_tag) et trace la migration via "
        "Produit.legacy_imported_as_produit_page."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--ids",
            nargs="+",
            type=int,
            help="Limiter la migration à ces ids de Produit.",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Exécute la migration puis annule la transaction.",
        )

    def handle(self, *args, **options):
        try:
            with transaction.atomic():
                self._run(options)
                if options["dry_run"]:
                    raise _Rollback
        except _Rollback:
            self.stdout.write(
                self.style.WARNING("Dry-run : toutes les écritures ont été annulées.")
            )

    def _run(self, options):
        try:
            index_page, created = get_or_create_legacy_index_page()
        except MigrationError as exc:
            raise CommandError(str(exc)) from exc
        if created:
            self.stdout.write(
                f"Index '{LEGACY_PRODUIT_INDEX_SLUG}' créé (id={index_page.pk})."
            )

        produits = Produit.objects.to_migrate().order_by("id")
        if options["ids"]:
            produits = produits.filter(id__in=options["ids"])
            missing = set(options["ids"]) - set(produits.values_list("id", flat=True))
            if missing:
                self.stdout.write(
                    self.style.WARNING(
                        f"Ids ignorés (déjà migrés, redirigés ou inconnus) : "
                        f"{sorted(missing)}"
                    )
                )

        migrated, failed = 0, []
        for produit in produits:
            try:
                with transaction.atomic():
                    report = migrate_produit(produit, index_page=index_page)
            except Exception as exc:  # noqa: BLE001
                failed.append((produit.pk, produit.nom, str(exc)))
                self.stdout.write(
                    self.style.ERROR(
                        f"Échec pour le produit {produit.nom} "
                        f"(id={produit.pk}) : {exc}"
                    )
                )
            else:
                migrated += 1
                suffix = f" ({report.details})" if report.details else ""
                self.stdout.write(
                    f"Produit {produit.nom} (id={produit.pk}) migré vers la page "
                    f"{report.page.slug} (id={report.page.pk}){suffix}"
                )

        self.stdout.write(
            self.style.SUCCESS(
                f"Migration terminée : {migrated} produit(s) migré(s), "
                f"{len(failed)} échec(s)."
            )
        )
