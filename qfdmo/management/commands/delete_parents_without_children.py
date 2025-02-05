import argparse

from django.core.management.base import BaseCommand
from django.db import connection

from qfdmo.models.acteur import RevisionActeur


class Command(BaseCommand):
    help = "Suppression des parents qui n'ont pas d'enfants"

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            help="Run command without writing changes to the database",
            action=argparse.BooleanOptionalAction,
            default=False,
        )

    def handle(self, *args, **options):
        dry_run = options["dry_run"]
        # execute a sql query
        sql = """
        SELECT revision_acteur.id
        FROM qfdmo_revisionacteur revision_acteur
        LEFT OUTER JOIN "qfdmo_revisionacteur" AS "child"
            ON ("revision_acteur"."id" = "child"."parent_id")
        LEFT OUTER JOIN "qfdmo_acteur" AS "acteur"
            ON ("revision_acteur"."id" = "acteur"."id")
        WHERE "acteur"."id" IS NULL
        GROUP BY "revision_acteur"."id"
        HAVING COUNT("child"."id") = 0;
        """
        with connection.cursor() as cursor:
            cursor.execute(sql)
            rows = cursor.fetchall()

        identifiants_uniques = [row[0] for row in rows]
        self.stdout.write(
            self.style.SUCCESS(f"Parents sans enfants: {identifiants_uniques}")
        )
        if not dry_run:
            RevisionActeur.objects.filter(id__in=identifiants_uniques).delete()
            self.stdout.write(
                self.style.SUCCESS(
                    f"Revision acteurs supprimés: {identifiants_uniques}"
                )
            )
