from django.core.management.base import BaseCommand

from core.utils import (
    create_schema_warehouse_public_in_webapp_db,
    create_schema_webapp_public_in_warehouse_db,
)


class Command(BaseCommand):
    def handle(self, *args, **options):
        """Setup postgres schemas required by dbt"""
        self.stdout.write(
            self.style.WARNING("Creating schema webapp_public in warehouse…")
        )
        create_schema_webapp_public_in_warehouse_db()
        self.stdout.write(
            self.style.SUCCESS("✅ Schema webapp_public in warehouse done")
        )

        self.stdout.write(
            self.style.WARNING("Creating schema warehouse_public in webapp…")
        )
        create_schema_warehouse_public_in_webapp_db()
        self.stdout.write(
            self.style.SUCCESS("✅ Schema warehouse_public in webapp done")
        )
