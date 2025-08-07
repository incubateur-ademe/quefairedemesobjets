from django.core.management.base import BaseCommand

from core.utils import (
    SQL_CREATE_EXTENSIONS,
    create_schema_warehouse_public_in_webapp_db,
    create_schema_webapp_public_in_warehouse_db,
)


class Command(BaseCommand):
    def handle(self, *args, **options):
        """Setup postgres schemas required by dbt"""
        # This command usually runs locally, where postgres runs in Docker.
        # Locally, the postgres port set for Django is different than the
        # one exposed by the container as we expose the 5432 port on 6543
        # port on the machine.
        # As the django server does not run in docker, we cannot use the same port
        # as the postgres server uses 5432 port internally.
        #
        # This logic could be removed if the django server was running in docker, but
        # this is not planned at the moment.

        self.stdout.write(
            self.style.WARNING("Creating schema webapp_public in warehouse…")
        )
        sql = create_schema_webapp_public_in_warehouse_db()
        self.stdout.write(self.style.WARNING(f"SQL: {SQL_CREATE_EXTENSIONS}"))
        self.stdout.write(self.style.WARNING(f"SQL: {sql}"))
        self.stdout.write(
            self.style.SUCCESS("✅ Schema webapp_public in warehouse done")
        )

        self.stdout.write(
            self.style.WARNING("Creating schema warehouse_public in webapp…")
        )
        sql = create_schema_warehouse_public_in_webapp_db()
        self.stdout.write(self.style.WARNING(f"SQL: {SQL_CREATE_EXTENSIONS}"))
        self.stdout.write(self.style.WARNING(f"SQL: {sql}"))
        self.stdout.write(
            self.style.SUCCESS("✅ Schema warehouse_public in webapp done")
        )
