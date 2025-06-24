from django.core.management.base import BaseCommand

from qfdmo.models import Acteur, RevisionActeur


class Command(BaseCommand):
    help = (
        "Applique la fonction title() aux adresses des acteurs"
        " (adresse, adresse_complement, ville)"
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--limit",
            help="Limite le nombre d'acteurs à traiter",
            type=int,
            default=None,
        )
        parser.add_argument(
            "--dry-run",
            help="Effectue un test sans sauvegarder les modifications",
            action="store_true",
        )

    def handle(self, *args, **options):
        limit = options.get("limit")
        dry_run = options.get("dry_run")

        if dry_run:
            self.stdout.write(
                self.style.WARNING(
                    "Mode test activé - aucune modification ne sera sauvegardée"
                )
            )

        count = 0
        modified_count = 0

        CHUNKS_SIZE = 1000
        for cls in [Acteur, RevisionActeur]:
            model_name = cls.__name__
            self.stdout.write(f"Traitement des {model_name}s...")

            queryset = cls.objects.all()
            if limit:
                queryset = queryset[:limit]

            for i in range(0, queryset.count(), CHUNKS_SIZE):
                chunk = queryset[i : i + CHUNKS_SIZE]

                for acteur in chunk:
                    count += 1
                    has_changes = False

                    if count % 1000 == 0:
                        self.stdout.write(f"Traité {count} acteurs/revisionacteurs")

                    for field in ["adresse", "adresse_complement", "ville"]:
                        current_value = getattr(acteur, field)
                        if current_value:
                            titled_value = current_value.title().strip(" -,;")
                            if titled_value != current_value:
                                has_changes = True
                                if not dry_run:
                                    setattr(acteur, field, titled_value)
                                else:
                                    self.stdout.write(
                                        f"  {model_name} {acteur.pk}: {field}"
                                        f" '{current_value}' -> '{titled_value}'"
                                    )

                    if has_changes:
                        modified_count += 1
                        if not dry_run:
                            try:
                                acteur.save()
                            except Exception as e:
                                self.stdout.write(
                                    self.style.ERROR(f"  {model_name} {acteur.pk}: {e}")
                                )
                                continue

        if dry_run:
            self.stdout.write(
                self.style.SUCCESS(
                    f"Test terminé : {modified_count} acteurs auraient été modifiés"
                    f" sur {count} traités"
                )
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(
                    f"Terminé : {modified_count} acteurs modifiés sur {count} traités"
                )
            )
