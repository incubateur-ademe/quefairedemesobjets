"""
Django management command to rename tables and update migration history.

This command:
1. Renames database tables by replacing the 'sites_faciles_' prefix with
   'sites_conformes_'
2. Updates django_migrations and django_content_type to reflect the new app labels

Important:
This command does not create/alter columns. If the installed `sites_conformes.*` apps
contain
newer migrations (e.g. adding fields), you still need to run `python manage.py migrate`
after the rename (or use --run-migrate).

Usage:
    python manage.py migrate_from_sites_faciles_experiment [--dry-run] [--no-input]
        [--run-migrate]
"""

from django.core.management import call_command
from django.core.management.base import BaseCommand
from django.db import connection, transaction
from django.db.migrations.executor import MigrationExecutor


class Command(BaseCommand):
    help = "Rename tables and migrations to use sites_conformes_ prefix"

    # Apps to migrate (from search-and-replace.yml)
    APPS_TO_MIGRATE = [
        "sites_faciles_blog",
        "sites_faciles_events",
        "sites_faciles_forms",
        "sites_faciles_content_manager",
        "sites_faciles_config",
        "sites_faciles_proconnect",
        "sites_faciles_dashboard",
    ]

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Preview changes without executing them",
        )
        parser.add_argument(
            "--no-input",
            action="store_true",
            help="Skip confirmation prompt",
        )
        parser.add_argument(
            "--run-migrate",
            action="store_true",
            help="Run Django migrations for migrated apps after renaming",
        )

    def handle(self, *args, **options):
        dry_run = options["dry_run"]
        no_input = options["no_input"]
        run_migrate = options["run_migrate"]

        new_apps = [
            app.replace("sites_faciles_", "sites_conformes_", 1)
            for app in self.APPS_TO_MIGRATE
        ]

        self.stdout.write(self.style.SUCCESS("Starting database rename operations..."))
        self.stdout.write("=" * 60)

        with connection.cursor() as cursor:
            # Step 1: Get list of tables to rename
            self.stdout.write("\n1. Finding tables to rename...")

            table_patterns = [f"{app}_%" for app in self.APPS_TO_MIGRATE]
            query = """
                SELECT table_name
                FROM information_schema.tables
                WHERE table_schema = 'public'
                  AND table_name LIKE ANY (%s)
                ORDER BY table_name;
            """
            cursor.execute(query, [table_patterns])

            tables_to_rename = cursor.fetchall()

            if not tables_to_rename:
                self.stdout.write(self.style.WARNING("No tables found to rename."))
                return

            self.stdout.write(
                self.style.SUCCESS(f"Found {len(tables_to_rename)} tables to rename:")
            )
            table_renames = []
            for (table_name,) in tables_to_rename:
                # Only replace the sites_faciles_ prefix, not inner occurrences
                new_name = table_name.replace("sites_faciles_", "sites_conformes_", 1)
                table_renames.append((table_name, new_name))
                self.stdout.write(f"  - {table_name} → {new_name}")

            # Step 2: Preview migration updates
            self.stdout.write("\n2. Previewing migration updates...")

            query = """
                SELECT
                    app,
                    COUNT(*) as migration_count
                FROM django_migrations
                WHERE app = ANY (%s)
                GROUP BY app
                ORDER BY app;
            """
            cursor.execute(query, [self.APPS_TO_MIGRATE])

            migrations_to_update = cursor.fetchall()

            if not migrations_to_update:
                self.stdout.write(self.style.WARNING("No migrations found to update."))
                migration_updates = []
            else:
                self.stdout.write(
                    self.style.SUCCESS(
                        f"Found migrations in {len(migrations_to_update)} apps:"
                    )
                )
                migration_updates = []
                for app, count in migrations_to_update:
                    new_app = app.replace("sites_faciles_", "sites_conformes_", 1)
                    migration_updates.append((app, new_app, count))
                    self.stdout.write(f"  - {app}: {count} migration(s) → {new_app}")

            if dry_run:
                self.stdout.write("\n" + "=" * 60)
                self.stdout.write(self.style.SUCCESS("DRY RUN: No changes were made."))
                return

            # Step 3: Confirm before proceeding
            if not no_input:
                self.stdout.write("\n" + "=" * 60)
                confirm = input("Proceed with renaming? (yes/no): ")
                if confirm.lower() != "yes":
                    self.stdout.write(self.style.WARNING("Operation cancelled."))
                    return

            self.stdout.write("\n3. Starting transaction...")

            with transaction.atomic():
                # Step 4: Rename tables
                self.stdout.write("\n4. Renaming tables...")
                renamed_count = 0
                rename_errors = []
                for table_name, new_name in table_renames:
                    try:
                        cursor.execute(
                            f'ALTER TABLE "{table_name}" RENAME TO "{new_name}";'
                        )
                        self.stdout.write(
                            self.style.SUCCESS(
                                f"  ✓ Renamed: {table_name} → {new_name}"
                            )
                        )
                        renamed_count += 1
                    except Exception as e:
                        rename_errors.append((table_name, new_name, e))
                        self.stdout.write(
                            self.style.ERROR(f"  ✗ Error renaming {table_name}: {e}")
                        )

                if rename_errors:
                    # Fail fast so the atomic transaction rolls back rather than leaving
                    # a partial rename.
                    raise RuntimeError(
                        "Aborting due to table rename errors: "
                        + ", ".join([f"{old}→{new}" for old, new, _ in rename_errors])
                    )

                self.stdout.write(
                    self.style.SUCCESS(f"\nRenamed {renamed_count} tables.")
                )

                # Step 5: Update django_migrations
                if migration_updates:
                    self.stdout.write("\n5. Updating django_migrations table...")

                    query = """
                        UPDATE django_migrations
                        SET app = REPLACE(app, 'sites_faciles_', 'sites_conformes_')
                        WHERE app = ANY (%s);
                    """
                    cursor.execute(query, [self.APPS_TO_MIGRATE])
                    updated_rows = cursor.rowcount
                    self.stdout.write(
                        self.style.SUCCESS(
                            f"  ✓ Updated {updated_rows} migration records"
                        )
                    )

                # Step 6: Update django_content_type
                self.stdout.write("\n6. Updating django_content_type table...")

                query = """
                UPDATE django_content_type
                SET app_label = REPLACE(app_label, 'sites_faciles_', 'sites_conformes_')
                WHERE app_label = ANY (%s);
                """
                cursor.execute(query, [self.APPS_TO_MIGRATE])
                updated_content_types = cursor.rowcount
                self.stdout.write(
                    self.style.SUCCESS(
                        f"  ✓ Updated {updated_content_types} content type records"
                    )
                )

            # Step 7: Verify changes
            self.stdout.write("\n7. Verifying changes...")

            # Verify migrations
            cursor.execute(
                """
                SELECT app, COUNT(*) as count
                FROM django_migrations
                WHERE app LIKE 'sites_conformes_%'
                GROUP BY app
                ORDER BY app;
            """
            )

            results = cursor.fetchall()
            if results:
                self.stdout.write("Migration records after update:")
                for app, count in results:
                    self.stdout.write(f"  - {app}: {count} migration(s)")

            # Verify content types
            cursor.execute(
                """
                SELECT app_label, COUNT(*) as count
                FROM django_content_type
                WHERE app_label LIKE 'sites_conformes_%'
                GROUP BY app_label
                ORDER BY app_label;
            """
            )

            ct_results = cursor.fetchall()
            if ct_results:
                self.stdout.write("\nContent type records after update:")
                for app_label, count in ct_results:
                    self.stdout.write(f"  - {app_label}: {count} model(s)")

            # Step 8: Show pending migrations for migrated apps (and optionally run
            # them)
            self.stdout.write("\n8. Checking pending migrations...")
            executor = MigrationExecutor(connection)
            targets = executor.loader.graph.leaf_nodes()
            plan = executor.migration_plan(targets)
            pending_for_new_apps = [
                (app, name) for app, name in plan if app in set(new_apps)
            ]

            if pending_for_new_apps:
                self.stdout.write(
                    self.style.WARNING(
                        "Pending migrations detected for migrated apps "
                        "(schema may be incomplete):"
                    )
                )
                for app, name in pending_for_new_apps:
                    self.stdout.write(f"  - {app}: {name}")
            else:
                self.stdout.write(
                    self.style.SUCCESS("No pending migrations for migrated apps.")
                )

            if run_migrate:
                self.stdout.write("\nRunning migrations for migrated apps...")
                for app_label in new_apps:
                    call_command("migrate", app_label, interactive=not no_input)

            self.stdout.write("\n" + "=" * 60)
            self.stdout.write(
                self.style.SUCCESS("✓ All operations completed successfully!")
            )
