from django.apps import apps
from django.core.management.base import BaseCommand
from django.db import transaction
from wagtail.blocks.migrations.migrate_operation import MigrateStreamData
from wagtail.blocks.migrations.operations import AlterBlockValueOperation

DECORATIVE = [(AlterBlockValueOperation(new_value=True), "image.decorative")]


class Command(BaseCommand):
    help = (
        "Coche « image décorative » sur toutes les images infotri existantes "
        "(ProduitPage, leurs révisions, et Produit legacy). Idempotent."
    )

    def handle(self, *args, **options):
        with transaction.atomic():
            for model_name in ("ProduitPage", "Produit"):
                # Reuse Wagtail's stream data migration, which also rewrites
                # the revisions of versioned models.
                MigrateStreamData(
                    "qfdmd", model_name, "infotri", DECORATIVE
                ).migrate_stream_data_forward(apps, None)
                self.stdout.write(
                    f"{model_name}.infotri : images marquées décoratives."
                )
