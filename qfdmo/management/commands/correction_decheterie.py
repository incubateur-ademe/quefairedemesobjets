"""
Correction des libellés déchetterie
"""

import argparse

from django.contrib.postgres.lookups import Unaccent
from django.core.management.base import BaseCommand
from django.db.models.functions import Lower

from qfdmo.models.acteur import Acteur, RevisionActeur, VueActeur


class Command(BaseCommand):
    help = "Test url availability and save proposition of correction"

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            help="Run command without writing changes to the database",
            action=argparse.BooleanOptionalAction,
            default=False,
        )

    def handle(self, *args, **options):
        dry_run = options.get("dry_run")
        count = 0

        decheterie_labels_fix = {
            "dechetterie": "déchèterie",
            "déchetterie": "déchèterie",
            "déchètterie": "déchèterie",
            "Dechetterie": "Déchèterie",
            "Déchetterie": "Déchèterie",
            "Déchètterie": "Déchèterie",
            "DECHETTERIE": "DÉCHÈTERIE",
            "DÉCHETTERIE": "DÉCHÈTERIE",
            "DÉCHÈTTERIE": "DÉCHÈTERIE",
        }
        # Manage nom
        for vueacteur in VueActeur.objects.annotate(
            nom_unaccent=Unaccent(Lower("nom")),
        ).filter(nom_unaccent__icontains="dechetterie"):
            revision = None
            vueacteur_label = vueacteur.nom
            identifiant_unique = vueacteur.identifiant_unique
            try:
                acteur = Acteur.objects.get(identifiant_unique=identifiant_unique)
                revision = acteur.get_or_create_revision()
            except Acteur.DoesNotExist:
                revision = RevisionActeur.objects.get(
                    identifiant_unique=identifiant_unique
                )

            for decheterie_label, decheterie_label_fix in decheterie_labels_fix.items():
                vueacteur_label = vueacteur_label.replace(
                    decheterie_label, decheterie_label_fix
                )
            revision.nom = vueacteur_label
            count += 1
            self.stdout.write(
                self.style.SUCCESS(
                    f"{dry_run and 'DRY RUN ' or ''}update nom: {identifiant_unique} -"
                    f" from {vueacteur.nom}"
                    f" to {revision.nom}"
                )
            )
            if not dry_run:
                revision.save()

        # Manage nom_commercial
        for vueacteur in VueActeur.objects.annotate(
            nom_commercial_unaccent=Unaccent(Lower("nom_commercial")),
        ).filter(nom_commercial_unaccent__icontains="dechetterie"):
            revision = None
            vueacteur_label = vueacteur.nom_commercial
            identifiant_unique = vueacteur.identifiant_unique
            try:
                acteur = Acteur.objects.get(identifiant_unique=identifiant_unique)
                revision = acteur.get_or_create_revision()
            except Acteur.DoesNotExist:
                revision = RevisionActeur.objects.get(
                    identifiant_unique=identifiant_unique
                )

            for decheterie_label, decheterie_label_fix in decheterie_labels_fix.items():
                vueacteur_label = vueacteur_label.replace(
                    decheterie_label, decheterie_label_fix
                )
            revision.nom_commercial = vueacteur_label
            count += 1
            self.stdout.write(
                self.style.SUCCESS(
                    f"{dry_run and 'DRY RUN ' or ''}update nom_commercial:"
                    f" {identifiant_unique} - from {vueacteur.nom_commercial}"
                    f" to {revision.nom_commercial}"
                )
            )
            if not dry_run:
                revision.save()

        print(f"Nb d'acteur modifier: {count}")
