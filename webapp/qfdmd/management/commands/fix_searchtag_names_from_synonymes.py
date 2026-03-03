from django.core.management.base import BaseCommand

from qfdmd.models import SearchTag


class Command(BaseCommand):
    help = "Replace SearchTag names with the original casing from their linked Synonyme.nom"

    def handle(self, *args, **options):
        tags = SearchTag.objects.filter(
            legacy_existing_synonyme__isnull=False
        ).select_related("legacy_existing_synonyme")

        updated = 0
        for tag in tags:
            synonyme = tag.legacy_existing_synonyme
            correct_name = synonyme.nom.replace(", ", "\uff0c").replace(",", "\uff0c")
            if tag.name != correct_name:
                tag.name = correct_name
                tag.save(update_fields=["name"])
                updated += 1

        self.stdout.write(f"Updated {updated} SearchTag name(s).")
